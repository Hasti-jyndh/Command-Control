#test2
from django.urls import path
from .views import *

urlpatterns = [
    path('',home,name='home'),
    path('agents/',agents,name='agents'),
    path('register/',register_agent, name='register_agent'),
    path('command/<str:agent_id>/', get_command, name='get_command'),
    path('report/<str:agent_id>/', report_result, name='report_result'),
    path('file/<uuid:agent_id>/<str:file_name>/', file_transfer, name='download_file'),
    path('file/<uuid:agent_id>/', file_transfer, name='upload_file'),
]

