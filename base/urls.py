from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentViewSet, CommandViewSet, ExecutedCommandViewSet, FileTransferViewSet
import uuid
# Initialize the router
router = DefaultRouter()

# Register the viewsets with the router
router.register(r'agents', AgentViewSet, basename='agent')
router.register(r'commands', CommandViewSet, basename='command')
router.register(r'executed_commands', ExecutedCommandViewSet, basename='executedcommand')
router.register(r'media', FileTransferViewSet, basename='filetransfer')

# Define the URL patterns
urlpatterns = [
    path('', include(router.urls)),  # Include all router-generated URLs
    path('agents/<uuid:agent_id>/', include(router.urls)),
]#/agents/<agentid>/commands/<id>
