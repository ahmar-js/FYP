from django.urls import path
from app import views

urlpatterns = [
    path('upload/', views.upload_view, name='upload'),
    path('preview/', views.upload_file, name='preview'),
    path('preview_data/', views.preview_data, name='preview_data'),
    path('handle_drop_columns/', views.handle_drop_columns, name='handle_drop_columns'),
    path('update_statistics/', views.update_statistics, name='update_statistics'),
    # path('describe_data/', views.describe_data, name='describe_data'),
    # path('preview_dataframe_ajax/', views.preview_dataframe_ajax, name='preview_dataframe_ajax'),
]
