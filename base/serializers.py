from rest_framework import serializers
from .models import *

class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = ['id', 'name', 'ip_address', 'last_seen']

class CommandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Command
        fields = ['id', 'agent', 'command_text', 'executed', 'output']

class FileTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileTransfer
        fields = ['id', 'agent', 'file', 'file_name', 'direction', 'status', 'timestamp']

class ExecutedCommandSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutedCommand
        fields = ['id', 'agent', 'command_text', 'output', 'executed_at']