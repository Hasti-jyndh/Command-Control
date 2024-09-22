from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Agent, Command, ExecutedCommand, FileTransfer
from .serializers import AgentSerializer, CommandSerializer, ExecutedCommandSerializer, FileTransferSerializer
from django.utils import timezone
from datetime import timedelta


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

    @action(detail=True, methods=['get'])
    def pending_files(self, request, pk=None):
        agent = self.get_object()
        files = agent.file_transfers.filter(direction='download', status='pending')
        return Response(FileTransferSerializer(files, many=True).data)

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

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        agent = self.get_object()
        agent.is_paused = True
        agent.save()
        return Response({"status": "Agent paused"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def unpause(self, request, pk=None):
        agent = self.get_object()
        agent.is_paused = False
        agent.save()
        return Response({"status": "Agent unpaused"}, status=status.HTTP_200_OK)


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

            # Move the command to ExecutedCommand model
            executed_command = ExecutedCommand.objects.create(
                agent=command.agent,
                command_text=command.command_text,
                output=command.output,
                timestamp=timezone.now()  # or use command's timestamp
            )

            # Delete the original command
            command.delete()

            # Return success response
            return Response({
                "status": "Command executed and agent last_seen updated",
                "executed_command": ExecutedCommandSerializer(executed_command).data
            }, status=status.HTTP_200_OK)

        return response

    # Alternatively, create a specific action to update the executed status and agent last_seen
    @action(detail=True, methods=['patch'])
    def set_command_executed(self, request, pk=None):
        command = self.get_object()

        # Mark command as executed
        command.executed = True
        command.output = request.data.get('output', '')  # Optionally get output from the request
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

        return Response(FileTransferSerializer(file_transfer).data, status=status.HTTP_201_CREATED)


def mark_agents_as_offline(self):
    agent = self.get_object()
    threshold_time = timezone.now() - timedelta(minutes=5)
    agent.objects.filter(last_check_in__lt=threshold_time).update(is_online=False)
