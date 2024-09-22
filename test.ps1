function Load-OrCreateAgentUUID {
    param (
        [string]$ConfigFile,
        [string]$AgentIP
    )
    
    # Check if the config file exists
    if (Test-Path $ConfigFile) {
        # Load the config file if it exists
        $config = Get-Content -Raw -Path $ConfigFile | ConvertFrom-Json
        return $config.uuid
    } else {
        # Generate a new UUID and create the config
        $agentUUID = [guid]::NewGuid().ToString()
        $config = @{
            uuid = $agentUUID
            name = "agent03"
            IPAddress = $AgentIP
        }
        # Save the config to the file
        $config | ConvertTo-Json | Set-Content -Path $ConfigFile
        return $agentUUID
    }
}

# Usage example
$ConfigFile = "path\to\config.json"
$AgentIP = "192.168.1.100"
$uuid = Load-OrCreateAgentUUID -ConfigFile $ConfigFile -AgentIP $AgentIP
Write-Output $uuid
