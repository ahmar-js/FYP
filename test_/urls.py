from django.urls import path
from app import views

urlpatterns = [
    path('', views.upload_file, name='upload_file'),
]
