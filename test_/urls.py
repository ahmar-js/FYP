from django.urls import path
from app import views

urlpatterns = [
    path('upload/', views.upload_view, name='upload'),
    path('preview/', views.upload_file, name='preview'),

]
