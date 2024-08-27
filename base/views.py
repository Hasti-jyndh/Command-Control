from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
import json
import uuid

def home(request):
    return render(request,'home.html')

def agents(request):
    return render(request,'agents.html')

@csrf_exempt
def register_agent(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        agent_id = str(uuid.uuid4())
        agent = Agent.objects.create(agent_id=agent_id, ip_address=request.META['REMOTE_ADDR'])
        return JsonResponse({'agent_id': agent.agent_id})

@csrf_exempt
def get_command(request, agent_id):
    try:
        agent = Agent.objects.get(agent_id=agent_id)
        command = Command.objects.filter(agent=agent, executed=False).first()
        if command:
            action = command.command_text
            file_id = None

            uploaded_file = UploadedFile.objects.filter(agent=agent).first()
            if uploaded_file:
                file_id = uploaded_file.id

            return JsonResponse({
                'action': action,
                'command_id': command.id,
                'file_id': file_id
            })
        else:
            return JsonResponse({'action': None, 'command_id': None, 'file_id': None})
    except Agent.DoesNotExist:
        return JsonResponse({'error': 'Agent not found'}, status=404)

@csrf_exempt
def report_result(request, agent_id):
    if request.method == 'POST':
        try:
            agent = Agent.objects.get(agent_id=agent_id)
            data = json.loads(request.body)
            command = Command.objects.get(id=data['command_id'])
            command.result = data['result']
            command.executed = True
            command.save()
            return JsonResponse({'status': 'ok'})
        except (Agent.DoesNotExist, Command.DoesNotExist):
            return JsonResponse({'error': 'Not found'}, status=404)


@csrf_exempt
def file_transfer(request, agent_id, file_name=None):
    try:
        agent = Agent.objects.get(agent_id=agent_id)

        # Handle file download
        if request.method == 'GET' and file_name:
            file_transfer = UploadedFile.objects.get(agent=agent, file__contains=file_name)
            return FileResponse(file_transfer.file, as_attachment=True, filename=file_name)

        # Handle file upload
        elif request.method == 'POST':
            if 'file' in request.FILES:
                uploaded_file = request.FILES['file']
                UploadedFile.objects.create(agent=agent, file=uploaded_file)
                return JsonResponse({'status': 'File uploaded successfully'})
            return JsonResponse({'error': 'No file provided'}, status=400)

    except Agent.DoesNotExist:
        return JsonResponse({'error': 'Agent not found'}, status=404)
    except UploadedFile.DoesNotExist:
        return JsonResponse({'error': 'File not found'}, status=404)

    return JsonResponse({'error': 'Invalid request method or parameters'}, status=400)