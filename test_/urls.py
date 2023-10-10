from django.conf import settings
from django.urls import path
from app import views as app_views
from django.contrib import admin
from visualization import views as viz_views
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),


    path('', app_views.upload_view, name='upload'),
    path('preview/', app_views.upload_file, name='preview'),
    path('preview_data/', app_views.preview_data, name='preview_data'),
    path('handle_drop_columns/', app_views.handle_drop_columns, name='handle_drop_columns'),
    path('update_statistics/', app_views.update_statistics, name='update_statistics'),
    path('download_csv/', app_views.download_csv, name='download_csv'),
    path('handle_fill_null_values/', app_views.handle_fill_null_values, name='handle_fill_null_values/'),
    path('handle_drop_rows/', app_views.handle_drop_rows, name='handle_drop_rows/'),
    path('convert_to_geodataframe/', app_views.convert_to_geodataframe, name='convert_to_geodataframe/'),
    path('getis_ord_gi_hotspot_analysis/', app_views.getis_ord_gi_hotspot_analysis, name='getis_ord_gi_hotspot_analysis/'),
    path('model_fb_prophet/', app_views.model_fb_prophet, name='model_fb_prophet/'),
    path('fetch_unique_districts/', app_views.fetch_unique_districts, name='fetch_unique_districts'),
    # path('export_fb_forecasted_csv/', app_views.export_fb_forecasted_csv, name='export_fb_forecasted_csv'),
    path('export_fb_cv_csv_zip/', app_views.export_fb_cv_csv_zip, name='export_fb_cv_csv_zip'),
    path('model_arima_family/', app_views.model_arima_family, name='model_arima_family'),
    path('export_arima_results/', app_views.export_arima_results, name='export_arima_results'),
    path('handle_data_type_conversion/', app_views.handle_data_type_conversion, name='handle_data_type_conversion'),
    path('handle_coordinate_system_conversion/', app_views.handle_coordinate_system_conversion, name='handle_coordinate_system_conversion'),


    #visualization
    path('home/', viz_views.home, name='home'),
    path('get_model_results/', viz_views.get_model_results, name='get_model_results'),
    # path('get_column_names/', viz_views.get_column_names, name='get_column_names'),
    path('Geodatafileselection/', viz_views.Geodatafileselection, name='Geodatafileselection'),
    path('retrieve_column_names/', viz_views.retrieve_column_names, name='retrieve_column_names'),
    path('retrieve_column_names_df/', viz_views.retrieve_column_names_df, name='retrieve_column_names_df'),
    path('get_prophet_results/', viz_views.get_prophet_results, name='get_prophet_results'),
    path('get_arima_results/', viz_views.get_arima_results, name='get_arima_results'),
    
    
    
    
    # path('get_geo_data/', viz_views.get_geo_data, name='get_geo_data'),
    # path('get_selected_gdf_data/', viz_views.get_selected_gdf_data, name='get_selected_gdf_data'),

    #Authentication
    path('Login/', app_views.Login, name='Login'),
    path('login_user/', app_views.login_user, name='login_user'),
    path('register/', app_views.register, name='register'),
    path('register_login/', app_views.register_login, name='register_login'),
    path('Logout/', app_views.Logout, name='Logout'),

    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),

    path('save_dataframe_to_database/', viz_views.save_dataframe_to_database, name='save_dataframe_to_database'),
]
    # path('generate_plot/', app_views.generate_plot, name='generate_plot'),

    # path('describe_data/', app_views.describe_data, name='describe_data'),
    # path('preview_dataframe_ajax/', app_views.preview_dataframe_ajax, name='preview_dataframe_ajax'),

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)