from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentViewSet, CommandViewSet, ExecutedCommandViewSet, FileTransferViewSet
from django.conf import settings
from django.conf.urls.static import static
import uuid
# Initialize the router
router = DefaultRouter()

# Register the viewsets with the router
router.register(r'agents', AgentViewSet, basename='agent')
router.register(r'commands', CommandViewSet, basename='command')
router.register(r'executed_commands', ExecutedCommandViewSet, basename='executedcommand')
router.register(r'uploads', FileTransferViewSet, basename='filetransfer')

# Define the URL patterns
urlpatterns = [
    path('', include(router.urls)),  # Include all router-generated URLs
    path('agents/<uuid:agent_id>/', include(router.urls)),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)