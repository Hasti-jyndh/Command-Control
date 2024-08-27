from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class Agent(models.Model):
    agent_id = models.CharField(max_length=50, unique=True)
    last_checkin = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return self.agent_id


class Command(models.Model):
    AGENT_COMMAND = 'cmd'
    UPLOAD_COMMAND = 'upload'
    DOWNLOAD_COMMAND = 'download'

    COMMAND_CHOICES = [
        (AGENT_COMMAND, 'Command'),
        (UPLOAD_COMMAND, 'Upload'),
        (DOWNLOAD_COMMAND, 'Download'),
    ]

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='commands')
    command_text = models.TextField()
    executed = models.BooleanField(default=False)
    result = models.TextField(blank=True, null=True)
    direction = models.CharField(max_length=10, choices=COMMAND_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Command for {self.agent.agent_id}: {self.command_text}"

class FileTransfer(models.Model):
    UPLOAD = 'upload'
    DOWNLOAD = 'download'

    DIRECTION_CHOICES = [
        (UPLOAD, 'Upload'),
        (DOWNLOAD, 'Download'),
    ]

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/')
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    transferred_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.direction.capitalize()} of {self.file_name} for {self.agent}"

@receiver(post_save, sender=FileTransfer)
def create_command_for_file_transfer(sender, instance, created, **kwargs):
    if created:
        command_text = f"{instance.direction.capitalize()} file: {instance.file_name}"
        Command.objects.create(
            agent=instance.agent,
            command_text=command_text,
            direction=instance.direction,
        )