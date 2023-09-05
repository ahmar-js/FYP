from django.urls import path
from app import views

urlpatterns = [
    path('upload/', views.upload_view, name='upload'),
    path('preview/', views.upload_file, name='preview'),
    path('preview_data/', views.preview_data, name='preview_data'),
    path('handle_drop_columns/', views.handle_drop_columns, name='handle_drop_columns'),
    path('update_statistics/', views.update_statistics, name='update_statistics'),
    path('download_csv/', views.download_csv, name='download_csv'),
    path('handle_fill_null_values/', views.handle_fill_null_values, name='handle_fill_null_values/'),
    path('handle_drop_rows/', views.handle_drop_rows, name='handle_drop_rows/'),
    path('convert_to_geodataframe/', views.convert_to_geodataframe, name='convert_to_geodataframe/'),
    path('getis_ord_gi_hotspot_analysis/', views.getis_ord_gi_hotspot_analysis, name='getis_ord_gi_hotspot_analysis/'),
    # path('generate_plot/', views.generate_plot, name='generate_plot'),

    # path('describe_data/', views.describe_data, name='describe_data'),
    # path('preview_dataframe_ajax/', views.preview_dataframe_ajax, name='preview_dataframe_ajax'),
]
