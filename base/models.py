from django.db import models

class Agent(models.Model):
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    last_seen = models.DateTimeField(auto_now=True)
    # TO DO
    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.name


class Command(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='commands')
    command_text = models.TextField()
    executed = models.BooleanField(default=False)
    output = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Command for {self.agent.name}"

class ExecutedCommand(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='executed_commands')
    command_text = models.TextField()
    output = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Executed Command for {self.agent.name} at {self.timestamp}"

class FileTransfer(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='file_transfers')
    file = models.FileField(upload_to='uploads/')
    file_name = models.CharField(max_length=255, blank=True)  # To store the original file name
    direction = models.CharField(max_length=10, choices=(('upload', 'Upload'), ('download', 'Download')))
    status = models.CharField(max_length=10, choices=(('pending', 'Pending'), ('completed', 'Completed')), default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FileTransfer ({self.direction}) for {self.agent.name}"
