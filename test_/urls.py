from django.urls import path
from app import views

urlpatterns = [
    path('upload/', views.upload_view, name='upload'),
    path('preview/', views.upload_file, name='preview'),
    path('preview_data/', views.preview_data, name='preview_data'),
    # path('preview_dataframe_ajax/', views.preview_dataframe_ajax, name='preview_dataframe_ajax'),
]

