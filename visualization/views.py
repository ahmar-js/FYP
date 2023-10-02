from datetime import datetime
import json
from django.contrib import messages
import os
from django.core.files import File
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.db import models
from django.core.management import call_command
from django.http import JsonResponse
from io import StringIO
import folium

import pandas as pd
from .models import Uploaded_DataFrame, geoDataFrame, fbProphet_forecasts, ARIMA_forecasts, ConfigDashboard
from django.apps import apps
from django.db import connection
import inspect
from django.contrib.auth.decorators import login_required
from app.json_serializable import json_to_geodataframe, json_to_dataframe, dataframe_to_json

def preview_dataframe(df, limit=10):
    return df.head(limit)

# @login_required(login_url='/Login/')
# def home(request):
#     periodfb = 0
#     freqfb = ''
#     uploaded_frame = Uploaded_DataFrame.objects.filter(user=request.user)
#     # filtered_fb_forecasted = fbProphet_forecasts.objects.filter(user=request.user)
#     # filtered_arima_forecasted = ARIMA_forecasts.objects.filter(user=request.user)
#     # filtered_fb_vals = filtered_fb_forecasted.values_list('filtered_by', flat=True).distinct()
#     # filtered_arima_vals = filtered_fb_forecasted.values_list('filtered_by', flat=True).distinct()

#     # for value in filtered_fb_forecasted:
#     #     periodfb = value.period
#     #     freqfb = value.frequency

#     # print(periodfb, freqfb)
#     df = pd.DataFrame()
#     df_rows=0
#     if request.method == 'POST':
#         selected_df = request.POST.get('selectDataset', None)
#         selected_model = request.POST.get('selectModel', None)
#         selected_filter = request.POST.get('selectFilter', None)
#         if selected_df:
#             # selected_file = request.FILES['selectDataset']
#             data = pd.read_csv('../FYP'+selected_df)
#             df = pd.DataFrame(data)
#             df_rows = int(df.shape[0])
#             print(selected_df)

#         # if selected_model:
#         #     if selected_model == 'fbprophet':
#         #         fb_period = request.session.get('forecasted_period_fb', None)
#         #         fb_freq = request.session.get('forecasted_freq_fb', None)
#         #         if fb_freq is not None and fb_period is not None:
#         #             if fb_freq == 'A':
#         #                 mode = 'years'
#         #             elif fb_freq == 'Q':
#         #                 mode = 'Quarters'
#         #             elif fb_freq == 'M':
#         #                 mode = 'Months'
#         #             elif fb_freq == 'W':
#         #                 mode = 'Weeks'
#         #             elif fb_freq == 'D':
#         #                 mode = 'Days'
#         #             elif fb_freq == 'H':
#         #                 mode = 'Hours'
#         #             elif fb_freq == 'T':
#         #                 mode = 'Minutes'
#         #             elif fb_freq == 'S':
#         #                 mode = 'Seconds'
#         #             elif fb_freq == 'L':
#         #                 mode = 'Milliseconds'
#         #             elif fb_freq == 'U':
#         #                 mode = 'Microseconds'
#         #             elif fb_freq == 'N':
#         #                 mode = 'Nanoseconds'

#         #             fb_period = int(fb_period)
#         #     elif selected_model == 'arima':
#         #         pass
#     context = {
#         'user_files': uploaded_frame,
#         # 'filtered_fb_vals': filtered_fb_vals,
#         # 'dataframe': preview_dataframe(df, limit=50),
#         # 'df_rows': df_rows,
#     }
#     return render(request, 'pages/index.html', context)

@login_required(login_url='/Login/')
def home(request):
    uploaded_frame = Uploaded_DataFrame.objects.filter(user=request.user)
    

    m = folium.Map(location=[30.3753,  69.3451], zoom_start=5)



        
        

    # if request.method == 'POST':
    #     selected_df_id = request.POST.get('selectDataset', None)
    #     selected_model = request.POST.get('selectModel', None)
    #     selected_filter = request.POST.get('selectFilter', None)
    #     selected_df = Uploaded_DataFrame.objects.get(id=selected_df_id)
    #     selected_df_url = selected_df.file.url
    #     selected_gdf = geoDataFrame.objects.filter(U_df_id = selected_df_id)
    #     selected_fb_result = fbProphet_forecasts.objects.filter(U_df_id = selected_df_id)
    #     selected_arima_result = ARIMA_forecasts.objects.filter(U_df_id = selected_df_id)
    #     filtered_fb_vals = selected_fb_result.values_list('filtered_by', flat=True)

    #     # print(selected_model)
    #     # print(filtered_fb_vals)

    #     for gdf_record in selected_gdf:
    #         print("gdf_file", gdf_record.file.name)

    #     if selected_df_url:
    #         data = pd.read_csv('../FYP'+selected_df_url)
    #         df = pd.DataFrame(data)
    #         df_rows = int(df.shape[0])

    #     for index, row in df.iterrows():
    #         lat = row['plat']
    #         long = row['plong']
    #         district = row['pdistrict']
    
    #         # Create a CircleMarker for each patient
    #         folium.CircleMarker(
    #             location=[lat, long],
    #             popup=district,
    #             radius=5,  # Adjust the radius as needed
    #             color='blue',  # Customize the marker color
    #             fill=True,
    #             fill_color='blue',  # Customize the fill color
    #         ).add_to(m)
    
    context = {
        'user_files': uploaded_frame,
        "map": m._repr_html_(),

        
    }
    return render(request, 'pages/index.html', context)

# fetch model results in sidenav
def get_model_results(request):
    geodata_check = False
    numeric_columns = []
    if request.method == 'POST':
        selected_dataset_id = request.POST.get('selectedDatasetId', None)
        request.session['selected_dataset_id'] = selected_dataset_id


        # Retrieve the selected dataset
        selected_dataset = Uploaded_DataFrame.objects.get(id=selected_dataset_id)
        # selected_geodataset = geoDataFrame.objects.get()
        selected_df_url = selected_dataset.file.url
        if selected_df_url:
            data = pd.read_csv('../FYP'+selected_df_url)
            df = pd.DataFrame(data)
            df_rows = int(df.shape[0])
            columns = df.columns.tolist()
            numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])]

        
        # Retrieve associated geodataframe columns 
        uploaded_gdf = geoDataFrame.objects.filter(U_df_id=selected_dataset_id)


        # Retrieve model results based on the selected dataset
        selected_fb_results = fbProphet_forecasts.objects.filter(U_df_id=selected_dataset_id)
        selected_arima_results = ARIMA_forecasts.objects.filter(U_df_id=selected_dataset_id)

        # Create a list to hold the model results
        model_results = []
        gdf_result = [] 

        # Add gdf records to the list
        for gdf_results in uploaded_gdf:
            gdf_result.append({
                'id': gdf_results.id,
                'file': gdf_results.file.name,
                'updated_at': gdf_results.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

        # Add fbProphet results to the list
        for fb_result in selected_fb_results:
            model_results.append({
                'id': fb_result.id,
                'file': fb_result.file.name,
                'updated_at': fb_result.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'model': 'fbprophet'  # Indicate that this is an FBProphet result
            })

        for arima_result in selected_arima_results:
            model_results.append({
                'id': arima_result.id,
                'file': arima_result.file.name,
                'updated_at': arima_result.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'model': 'arima'  # Indicate that this is an ARIMA result
            })

        # print(model_results)
        json_response = {
            'modelResults': model_results,
            'gdf_results': gdf_result,
            'numeric_columns': numeric_columns,
            'df_columns': columns,
            'dataframe': preview_dataframe(df, limit=50).to_html(classes='table fade-out align-items-center table-flush') ,
            'df_rows': df_rows,
        }

        return JsonResponse({'message': 'Successs', 'json_response': json_response})
    

    # Handle other HTTP methods or invalid requests
    return JsonResponse({'error': 'Invalid request'})


def Geodatafileselection(request):
    geodata_check = True
    if request.method == 'POST':
        selected_geo_id = request.POST.get('Select_geodataframe', None)


        request.session['selected_geodataset_id'] = selected_geo_id

        # Retrieve the selected dataset
        selected_dataset = geoDataFrame.objects.get(id=selected_geo_id)
        # selected_geodataset = geoDataFrame.objects.get()
        selected_df_url = selected_dataset.file.url
        if selected_df_url:
            data = pd.read_csv('../FYP'+selected_df_url)
            df = pd.DataFrame(data)
            df_rows = int(df.shape[0])
            columns = df.columns.tolist()
            numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])]
        retrieve_column_names(request, selected_geo_id, geodata_check)

        json_response = {
            'numeric_columns': numeric_columns,
            'gdf_columns': columns,
            'gdataframe': preview_dataframe(df, limit=50).to_html(classes='table fade-out align-items-center table-flush'),
            'gdf_rows': df_rows,
        }

        return JsonResponse({'message': 'Successs', 'json_response': json_response})
    

    # Handle other HTTP methods or invalid requests
    return JsonResponse({'error': 'Invalid request'})
        





def retrieve_column_names(request, selected_dataset_id, geodata_check):
    if selected_dataset_id is not None:
        try:
            if geodata_check:
                column_record = ConfigDashboard.objects.get(U_gdf=selected_dataset_id)
            else:
                column_record = ConfigDashboard.objects.get(U_df=selected_dataset_id)
        except ConfigDashboard.DoesNotExist:
            column_record = None
            # messages.error(request, 'No records found for the specified dataset_id')
        if column_record is not None:
            long = column_record.longitude
            lat = column_record.latitude
            filtered = column_record.filtered
            color = column_record.color
            location = column_record.location
            hover_data = column_record.hover_data
            date = column_record.date
            size = column_record.size
            print(long, lat, filtered, color, location, hover_data, date, size)
            if color == 'hotspot_analysis':
                pass



# get column names and store them in database
def get_column_names(request):
    if request.method == 'POST':
        selected_X = request.POST.get('conf_select_x', None)
        selected_Y = request.POST.get('conf_select_y', None)
        filtered = request.POST.get('select_filtered_col', None)
        color = request.POST.get('select_color_col', None)
        location = request.POST.get('select_location_col', None)
        hover_data = request.POST.get('select_hover_data_col', None)
        date = request.POST.get('select_date', None)
        size = request.POST.get('select_size', None)
        done_hotspot = request.POST.get('done_hotspot', False)
        selected_df_id = request.session.get('selected_dataset_id', None)
        selected_gdf_id = request.session.get('selected_geodataset_id', None)
        if selected_gdf_id:
            selected_df = geoDataFrame.objects.get(U_df_id=selected_gdf_id)
            # Clear the 'selected_dataset_id' session variable
            if 'selected_dataset_id' in request.session or 'selected_geodataset_id' in request.session:
                del request.session['selected_dataset_id']
                del request.session['selected_geodataset_id']
            print("here")
        else:
            selected_df = Uploaded_DataFrame.objects.get(id=selected_df_id)
            if 'selected_dataset_id' in request.session or 'selected_geodataset_id' in request.session:
                del request.session['selected_dataset_id']
                del request.session['selected_geodataset_id']
        if done_hotspot:
            color = 'hotspot_analysis'
        save_columns_to_database(selected_df, selected_X, selected_Y, filtered, location, hover_data, date, size, color)


    return render(request, 'pages/index.html')
    

    
def save_columns_to_database(selected_df_instance, selected_X, selected_Y, filtered, location, hover_data, date, size, color):
# Query the database to check if a record with the same selected_df_instance exists
    existing_record = ConfigDashboard.objects.filter(U_df=selected_df_instance).first()

    if existing_record:
        # If a record exists, update its fields
        existing_record.latitude = selected_Y
        existing_record.longitude = selected_X
        existing_record.filtered = filtered
        existing_record.location = location
        existing_record.hover_data = hover_data
        existing_record.date = date
        existing_record.size = size
        existing_record.color = color
        existing_record.save()  # Save the updated record
    else:
        # If no record exists, create a new record
        config_dashboard_instance = ConfigDashboard(
            U_df=selected_df_instance,
            latitude=selected_Y,
            longitude=selected_X,
            filtered=filtered,
            location=location,
            hover_data=hover_data,
            date=date,
            size=size,
            color=color
        )
        config_dashboard_instance.save()  # Save the new record
    



def save_dataframe_to_database(request, df, name):
    # Generate a timestamp to append to the filename
    # timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = name

    if file_name == 'Hotspot_Analysis_File.csv':
        model_name = geoDataFrame
        my_file_instance = model_name()
        existing_file = None

    else:
        model_name = Uploaded_DataFrame
        my_file_instance = model_name(user=request.user)
        existing_file = model_name.objects.filter(user=request.user, file__contains=file_name).first()




    if existing_file is not None:
        print("existing file: ", existing_file.file.name)
        # Delete the existing file from the database
        existing_file.delete()



    # Create a path for the CSV file within the app's media folder
    media_path = os.path.join(settings.MEDIA_ROOT, file_name)

    if os.path.exists(media_path):
        os.remove(media_path)

    # Save the DataFrame to the CSV file
    df.to_csv(media_path, index=False)
    with open(media_path, 'rb') as file:
        my_file_instance.file.save(file_name, File(file))

    if model_name == geoDataFrame:
       # Set the U_df to the ID of the last record in Uploaded_DataFrame
       last_uploaded_df = Uploaded_DataFrame.objects.latest('id')
       my_file_instance.U_df = last_uploaded_df
    
    my_file_instance.save()

    return HttpResponse("CSV file uploaded to the database successfully.")

def save_forecasts_dataframe_to_db(request, df, name, filtered_by_val=[], period=None, freq=None):
    # Generate a timestamp to append to the filename
    # timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filtered_by_val = str(filtered_by_val)  # Convert to JSON string
    if filtered_by_val == '[]':
        filtered_by_val = 'Unfiltered'
    file_name = name + '_' + filtered_by_val + '.csv'

    if name == 'FB_Forecasts_File':
        model_name = fbProphet_forecasts
        if freq is not None and period is not None:
            my_file_instance = model_name(filtered_by=filtered_by_val, period=period, frequency=freq)

    else:
        model_name = ARIMA_forecasts
        if period is not None:
            my_file_instance = model_name(filtered_by=filtered_by_val, period=period)


    

    # Check if a file with the same name exists in the database
    existing_file = model_name.objects.filter(file__contains=file_name, filtered_by=filtered_by_val, period=period, U_df__user=request.user).first()

    if existing_file:
        print("existing file: ", existing_file.file.name)
        # Delete the existing file from the database
        existing_file.delete()

    # Create a path for the CSV file within the app's media folder
    media_path = os.path.join(settings.MEDIA_ROOT, file_name)

    if os.path.exists(media_path):
        os.remove(media_path)

    # Save the DataFrame to the CSV file
    df.to_csv(media_path, index=False)
    with open(media_path, 'rb') as file:
        my_file_instance.file.save(file_name, File(file))

    if model_name == fbProphet_forecasts or model_name == ARIMA_forecasts:
       # Set the U_df_id to the ID of the last record in Uploaded_DataFrame
       last_uploaded_df = Uploaded_DataFrame.objects.latest('id')
       my_file_instance.U_df = last_uploaded_df
    
    my_file_instance.save()

    return HttpResponse("CSV file uploaded to the database successfully.")

       