from django.contrib import admin
from .models import *
from django.http import HttpResponse
import os
from django.utils.encoding import smart_str


class CommandInline(admin.TabularInline):
    model = Command
    extra = 1


class AgentAdmin(admin.ModelAdmin):
    list_display = ('agent_id', 'last_checkin', 'ip_address')
    inlines = [CommandInline]
    search_fields = ('agent_id',)  # Allow searching by agent ID

class CommandAdmin(admin.ModelAdmin):
    list_display = ('agent', 'command_text', 'executed', 'result', 'direction', 'created_at')
    list_filter = ('executed', 'direction', 'created_at')
    search_fields = ('command_text', 'agent__agent_id')  # Search by agent ID as well
    readonly_fields = ('created_at',)  # Make created_at read-only
    ordering = ('-created_at',)  # Order by created_at descending

class FileTransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'agent', 'file_name', 'direction', 'transferred_at')
    search_fields = ('file_name', 'agent__agent_id', 'agent__ip_address')
    list_filter = ('direction', 'transferred_at')
    ordering = ('-transferred_at',)
    readonly_fields = ('transferred_at',)

    def file_name(self, obj):
        return obj.file.name

    def download_file(self, request, queryset):
        if queryset.count() == 1:
            obj = queryset.first()
            file_path = obj.file.path
            file_name = os.path.basename(file_path)
            with open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type="application/force-download")
                response['Content-Disposition'] = f'attachment; filename={smart_str(file_name)}'
                return response
        else:
            return HttpResponse("Select only one file to download at a time.", status=400)

    download_file.short_description = "Download selected file"


admin.site.register(Agent, AgentAdmin)
admin.site.register(Command, CommandAdmin)
admin.site.register(FileTransfer, FileTransferAdmin)