from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Agent, Command, ExecutedCommand, FileTransfer
from .serializers import AgentSerializer, CommandSerializer, ExecutedCommandSerializer, FileTransferSerializer
from django.utils import timezone
import base64,json

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer

    def create(self, request, *args, **kwargs):
        agent_uuid = request.data.get('uuid')
        agent_name = request.data.get('name')
        agent_ip = request.data.get('ip_address')
        existing_agent = Agent.objects.filter(name=agent_name, ip_address=agent_ip).first()
        if existing_agent:
            return Response({
                'id': existing_agent.id,
                'message': 'Agent reconnected to the existing registration.'
            }, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['patch'])
    def update_command(self, request, pk=None):
        agent = self.get_object()
        timestamp = request.data.get('timestamp')
        if timestamp:
            agent.last_seen = timezone.datetime.fromtimestamp(float(timestamp))
            agent.save()
        # Handle other command update logic here
        return Response({"status": "Command updated"}, status=status.HTTP_200_OK)
    @action(detail=True, methods=['post'])
    def add_command(self, request, pk=None):
        agent = self.get_object()
        command_text = request.data.get('command_text')
        command = Command.objects.create(agent=agent, command_text=command_text)
        agent.last_seen = timezone.now()
        agent.save(update_fields=['last_seen'])
        return Response(CommandSerializer(command).data)

    @action(detail=True, methods=['get'])
    def commands(self, request, pk=None):
        agent = self.get_object()
        commands = agent.commands.all()
        return Response(CommandSerializer(commands, many=True).data)

    @action(detail=True, methods=['patch'])
    def update_last_seen(self, request, pk=None):
        agent = self.get_object()
        timestamp = request.data.get('timestamp')
        if timestamp:
            agent.last_seen = timezone.datetime.fromtimestamp(float(timestamp))
            agent.save()
            return Response({"status": "Agent last_seen updated"}, status=status.HTTP_200_OK)
        return Response({"error": "Timestamp not provided"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def assign_file(self, request, pk=None):
        agent = self.get_object()
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file_transfer = FileTransfer.objects.create(
            agent=agent,
            file=file,
            file_name=file.name,
            direction='download'
        )
        return Response(FileTransferSerializer(file_transfer).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get','post'])
    def pending_files(self, request, pk=None):
        if request.method == "GET":
            agent = self.get_object()
            files = agent.file_transfers.filter(status='pending')
            return Response(FileTransferSerializer(files, many=True).data)
        elif request.method == "POST":
            agent = self.get_object()
            data = json.loads(request.body)
            counter = data.get('counter', 0)  # Total number of chunks
            chunk_data = data.get('chunkData')  # Single chunk data
            chunk_index = data.get('chunkIndex', -1)  # Current chunk index
            if not chunk_data or chunk_index == -1:
                return Response({'error': 'Invalid chunk data or index'}, status=status.HTTP_400_BAD_REQUEST)

            file_transfer = agent.file_transfers.filter(status='pending').first()
            if not file_transfer:
                file_transfer = agent.file_transfers.create(status='pending')
            try:
                decoded_chunk = base64.b64decode(chunk_data)  # Decode the base64 chunk into binary data
            except (TypeError, ValueError) as e:
                return Response({'error': 'Invalid base64 encoding'}, status=status.HTTP_400_BAD_REQUEST)

            with open(file_transfer.file_name, 'ab') as f:
                f.write(decoded_chunk)

            if chunk_index + 1 == counter:
                file_transfer.status = 'completed'
                file_transfer.transferred = True
                file_transfer.save()

            return Response({'message': 'Chunk uploaded successfully'}, status=status.HTTP_201_CREATED)

    # offline agent handling
    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        agent = self.get_object()
        agent.last_check_in = timezone.now()
        agent.is_online = True
        agent.save()
        return Response({"status": "Agent checked in"}, status=status.HTTP_200_OK)


class CommandViewSet(viewsets.ModelViewSet):
    queryset = Command.objects.all()
    serializer_class = CommandSerializer

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        # Check if the command was executed and move it to ExecutedCommand
        if response.data['executed']:
            command = self.get_object()
            ExecutedCommand.objects.create(
                agent=command.agent,
                command_text=command.command_text,
                output=command.output
            )
            #agent = self.get_object()
            agent = Agent.objects.get(id=kwargs.get('agent_id'))
            agent.last_seen = timezone.datetime.now()
            command.executed = True
            agent.save()
            command.save()
            command.delete()  # Remove the original command

        return response

    @action(detail=True, methods=['patch'])
    def update_last_seen(self, request, pk=None):
        agent = self.get_object()
        timestamp = request.data.get('timestamp')
        if timestamp:
            agent.last_seen = timezone.datetime.fromtimestamp(float(timestamp))
            agent.save()
            return Response({"status": "Agent last_seen updated"}, status=status.HTTP_200_OK)
        return Response({"error": "Timestamp not provided"}, status=status.HTTP_400_BAD_REQUEST)


class ExecutedCommandViewSet(viewsets.ModelViewSet):
    queryset = ExecutedCommand.objects.all()
    serializer_class = ExecutedCommandSerializer

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)

        # Check if the command was executed
        if response.data.get('executed'):
            command = self.get_object()

            # Update agent's last seen
            command.agent.last_seen = timezone.now()
            command.agent.save()
            # Delete the original command
            command.delete()
        return response

    @action(detail=True, methods=['patch'])
    def set_command_executed(self, request, pk=None):
        command = self.get_object()

        # Mark command as executed
        command.executed = True
        command.output = request.data.get('output', '')
        command.save()

        # Update agent's last_seen to the current time
        command.agent.last_seen = timezone.now()
        command.agent.save()

        # Move the command to ExecutedCommand model
        executed_command = ExecutedCommand.objects.create(
            agent=command.agent,
            command_text=command.command_text,
            output=command.output,
            timestamp=timezone.now()
        )

        # Delete the original command after moving it
        command.delete()

        return Response({
            "status": "Command executed and agent last_seen updated",
            "executed_command": ExecutedCommandSerializer(executed_command).data
        }, status=status.HTTP_200_OK)


class FileTransferViewSet(viewsets.ModelViewSet):
    queryset = FileTransfer.objects.all()
    serializer_class = FileTransferSerializer

    def create(self, request, *args, **kwargs):
        agent_id = request.data.get('agent')
        direction = request.data.get('direction')
        file = request.FILES.get('file')
        agent = Agent.objects.get(pk=agent_id)
        file_transfer = FileTransfer.objects.create(agent=agent, direction=direction, file=file, file_name=file.name)
        agent.last_seen = timezone.now()
        agent.save(update_fields=['last_seen'])
        return Response(FileTransferSerializer(file_transfer).data, status=status.HTTP_201_CREATED)
