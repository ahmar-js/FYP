from datetime import datetime
import json
import os
from django.core.files import File
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.db import models
from django.core.management import call_command
from io import StringIO

import pandas as pd
from .models import Uploaded_DataFrame, geoDataFrame, fbProphet_forecasts, ARIMA_forecasts
from django.apps import apps
from django.db import connection
import inspect
from django.contrib.auth.decorators import login_required
from app.json_serializable import json_to_geodataframe, json_to_dataframe, dataframe_to_json

def preview_dataframe(df, limit=10):
    return df.head(limit)

@login_required(login_url='/Login/')
def home(request):
    periodfb = 0
    freqfb = ''
    uploaded_frame = Uploaded_DataFrame.objects.filter(user=request.user)
    filtered_fb_forecasted = fbProphet_forecasts.objects.filter(user=request.user)
    filtered_arima_forecasted = ARIMA_forecasts.objects.filter(user=request.user)
    filtered_fb_vals = filtered_fb_forecasted.values_list('filtered_by', flat=True).distinct()
    filtered_arima_vals = filtered_fb_forecasted.values_list('filtered_by', flat=True).distinct()

    for value in filtered_fb_forecasted:
        periodfb = value.period
        freqfb = value.frequency

    print(periodfb, freqfb)
    df = pd.DataFrame()
    df_rows=0
    if request.method == 'POST':
        selected_df = request.POST.get('selectDataset', None)
        selected_model = request.POST.get('selectModel', None)
        selected_filter = request.POST.get('selectFilter', None)
        if selected_df:
            # selected_file = request.FILES['selectDataset']
            data = pd.read_csv('../FYP'+selected_df)
            df = pd.DataFrame(data)
            df_rows = int(df.shape[0])
            print(selected_df)

        if selected_model:
            if selected_model == 'fbprophet':
                fb_period = request.session.get('forecasted_period_fb', None)
                fb_freq = request.session.get('forecasted_freq_fb', None)
                if fb_freq is not None and fb_period is not None:
                    if fb_freq == 'A':
                        mode = 'years'
                    elif fb_freq == 'Q':
                        mode = 'Quarters'
                    elif fb_freq == 'M':
                        mode = 'Months'
                    elif fb_freq == 'W':
                        mode = 'Weeks'
                    elif fb_freq == 'D':
                        mode = 'Days'
                    elif fb_freq == 'H':
                        mode = 'Hours'
                    elif fb_freq == 'T':
                        mode = 'Minutes'
                    elif fb_freq == 'S':
                        mode = 'Seconds'
                    elif fb_freq == 'L':
                        mode = 'Milliseconds'
                    elif fb_freq == 'U':
                        mode = 'Microseconds'
                    elif fb_freq == 'N':
                        mode = 'Nanoseconds'

                    fb_period = int(fb_period)
            elif selected_model == 'arima':
                pass
    context = {
        'user_files': uploaded_frame,
        'filtered_fb_vals': filtered_fb_vals,
        'dataframe': preview_dataframe(df, limit=50),
        'df_rows': df_rows,
    }
    return render(request, 'pages/index.html', context)




def save_dataframe_to_database(request, df, name):
    # Generate a timestamp to append to the filename
    # timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = name

    if file_name == 'Hotspot_Analysis_File.csv':
        model_name = geoDataFrame
    else:
        model_name = Uploaded_DataFrame

    # Check if a file with the same name exists in the database
    existing_file = model_name.objects.filter(user=request.user, file__contains=file_name).first()

    if existing_file:
        print("existing file: ", existing_file.file.name)
        # Delete the existing file from the database
        existing_file.delete()

    # Create a new instance of model_name
    my_file_instance = model_name(user=request.user)

    # Create a path for the CSV file within the app's media folder
    media_path = os.path.join(settings.MEDIA_ROOT, file_name)

    if os.path.exists(media_path):
        os.remove(media_path)

    # Save the DataFrame to the CSV file
    df.to_csv(media_path, index=False)
    with open(media_path, 'rb') as file:
        my_file_instance.file.save(file_name, File(file))
    
    my_file_instance.save()

    return HttpResponse("CSV file uploaded to the database successfully.")

def save_forecasts_dataframe_to_db(request, df, name, filtered_by_val=[], freq=None, period=None):
    # Generate a timestamp to append to the filename
    # timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filtered_by_val = str(filtered_by_val)  # Convert to JSON string
    if filtered_by_val == '[]':
        filtered_by_val = 'Unfiltered'
    file_name = name + '_' + filtered_by_val + '.csv'

    if name == 'FB_Forecasts_File':
        model_name = fbProphet_forecasts
    else:
        model_name = ARIMA_forecasts

    

    # Check if a file with the same name exists in the database
    existing_file = model_name.objects.filter(user=request.user, file__contains=file_name).first()

    if existing_file:
        print("existing file: ", existing_file.file.name)
        # Delete the existing file from the database
        existing_file.delete()

    if freq is not None and period is not None:
        my_file_instance = model_name(user=request.user, filtered_by=filtered_by_val, period=period, frequency=freq)
    else:
        # Create a new instance of model_name
        my_file_instance = model_name(user=request.user, filtered_by=filtered_by_val)

    # Create a path for the CSV file within the app's media folder
    media_path = os.path.join(settings.MEDIA_ROOT, file_name)

    if os.path.exists(media_path):
        os.remove(media_path)

    # Save the DataFrame to the CSV file
    df.to_csv(media_path, index=False)
    with open(media_path, 'rb') as file:
        my_file_instance.file.save(file_name, File(file))
    
    my_file_instance.save()

    return HttpResponse("CSV file uploaded to the database successfully.")

       