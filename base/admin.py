from django.contrib import admin
from .models import Agent, Command, ExecutedCommand, FileTransfer

class CommandInline(admin.TabularInline):
    model = Command
    extra = 1
    readonly_fields = ('executed', 'output')

class ExecutedCommandInline(admin.TabularInline):
    model = ExecutedCommand
    extra = 1
    readonly_fields = ('command_text', 'output', 'timestamp')

class FileTransferInline(admin.TabularInline):
    model = FileTransfer
    extra = 1
    readonly_fields = ('direction', 'status', 'timestamp')

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip_address', 'last_seen')
    search_fields = ('name', 'ip_address')
    inlines = [CommandInline, ExecutedCommandInline, FileTransferInline]

@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ('agent', 'command_text', 'executed')
    list_filter = ('executed',)
    search_fields = ('command_text', 'agent__name')
    readonly_fields = ('executed', 'output')

@admin.register(ExecutedCommand)
class ExecutedCommandAdmin(admin.ModelAdmin):
    list_display = ('agent', 'command_text', 'timestamp')
    search_fields = ('command_text', 'agent__name')
    readonly_fields = ('command_text', 'output', 'timestamp')

@admin.register(FileTransfer)
class FileTransferAdmin(admin.ModelAdmin):
    list_display = ('agent', 'file_name', 'direction', 'status', 'timestamp')
    list_filter = ('direction', 'status')
    search_fields = ('file_name', 'agent__name')
    readonly_fields = ('timestamp',)