from datetime import datetime
import warnings
# Filter out specific warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*The 'nopython' keyword.*")
import re
import zipfile
import pickle
from pmdarima import auto_arima

from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required

import re
import json
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objs as go
from sklearn.metrics import mean_absolute_error, mean_squared_error
from prophet.diagnostics import cross_validation
from prophet.diagnostics import performance_metrics
from prophet.plot import plot_cross_validation_metric
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
import geopandas as gpd
import io
import statsmodels.api as sm
import base64
from prophet.plot import plot_plotly, plot_components_plotly
from prophet import Prophet
from pysal.lib import weights
from pysal.explore import esda
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from .data_preprocessing import read_csv_file, drop_selected_column, handle_missing_values, drop_rows, convert_column_data_type, convert_lat_lon_columns
from .projected_coordinate_systems import utm_to_lat_lon, feet_to_meter, km_to_meter
from .geographical_coordinate_system import convert_dms_to_decimal
from .Geooding import convert_lat_lng_to_addresses, concatenate_and_geocode
from .json_serializable import dataframe_to_json, json_to_dataframe, geodataframe_to_json, json_to_geodataframe
from django.http import JsonResponse
from visualization.views import save_dataframe_to_database, save_forecasts_dataframe_to_db


#================ For custom preview data limiter ================
def preview_dataframe(df, limit=10):
    return df.head(limit)

def dataframe_to_Geodataframe(df, x_column, y_column):
    if not df.empty and x_column is not None and y_column is not None:
        if x_column not in df.columns or y_column not in df.columns:
            raise ValueError('Selected columns do not exist in the DataFrame')

        # Check if the X and Y columns are of type float
        if df[x_column].dtype != 'float64' or df[y_column].dtype != 'float64':
            raise ValueError(f'X and Y must be of type float. Selected <b>{x_column}</b> and <b>{y_column}</b>')

        # Create a GeoDataFrame using the selected columns
        data = df
        gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data[x_column], data[y_column]))

        # Drop rows with missing geometries
        gdf = gdf.dropna(subset=["geometry"])

        # Check if the resulting GeoDataFrame is empty
        if gdf.empty:
            raise ValueError('GeoDataFrame is empty after dropping rows with missing geometries')

    return gdf




# def preview_dataframe(df, limit=10):
#     return df.head(limit)

def update_stats(df):
    preview_data = preview_dataframe(df)
    num_rows = df.shape[0]
    num_cols = df.shape[1]
    total_nulls = df.isnull().sum().sum()
    total_notnull = df.notnull().sum().sum()
    unique_dtypes = len(df.dtypes.unique())
    df_dtype_info = df.dtypes

        
    return preview_data, num_rows, num_cols, total_nulls, total_notnull, unique_dtypes, df_dtype_info

def update_statss(df):
    preview_data = preview_dataframe(df)
    num_rows = df.shape[0]
    num_cols = df.shape[1]
    total_nulls = df.isnull().sum().sum()
    total_notnull = df.notnull().sum().sum()
    describe_data = df.describe().to_html(classes='table table-hover table-bordered table-striped')
    # Calculate unique value counts for each column
    unique_value_counts = df.nunique()
    unique_counts_html = unique_value_counts.to_frame(name='Unique Values').to_html(classes='table table-hover table-striped table-bordered')
    null_colwise = df.isnull().sum()
    null_colwise_html = null_colwise.to_frame(name='Null Values').to_html(classes='table table-hover table-striped table-bordered')
    nonnull_colwise = df.notnull().sum()
    nonnull_colwise_df = nonnull_colwise.to_frame(name='Not Null Values')
    nonnull_colwise_html = nonnull_colwise_df.to_html(classes='table table-hover table-striped table-bordered')
    preview_datatypes = preview_data.dtypes.to_frame()
    # Reset the index
    preview_datatypes = preview_datatypes.reset_index()
    # Rename the columns to match your requirements
    preview_datatypes.columns = ['Column Name', 'Data Types']
    preview_datatypes_html = preview_datatypes.to_html(classes='table table-hover table-light  mb-0')


    # df_dtype_info = df_dtype_info.apply(lambda x: int(x) if np.issubdtype(x, np.integer) else x)
    
    stats = {
        'num_rows': str(num_rows),
        'num_cols': str(num_cols),
        'total_nulls': str(total_nulls),
        'total_notnull': str(total_notnull),
    }
    
    
    return preview_data, preview_datatypes_html, stats, describe_data, unique_counts_html, null_colwise_html, nonnull_colwise_html
@login_required(login_url='/Login/')
def upload_view(request):
    # request.session.clear()  # Clear the entire session
    uploaded_file_name = None
    if request.method == 'POST' and request.FILES.get('csv_file'):
        json_pred_df = request.session.get('prediction_dataframe')
        if json_pred_df:
            del request.session['prediction_dataframe']
        json_geodata = request.session.get('geodata_frame')
        if json_geodata:
            del request.session['geodata_frame']
        try:
            csv_file = request.FILES['csv_file']
            uploaded_file_name = csv_file.name  # Store the file name
            request.session['uploaded_file_name'] = uploaded_file_name
            df = read_csv_file(csv_file)
            # prev_df = df

            # Store the DataFrame in session
            request.session['data_frame'] = dataframe_to_json(df)

            # Store the original DataFrame in the session
            request.session['original_data_frame'] = dataframe_to_json(df)

            # Redirect to the preview view
            return redirect('preview')
        except Exception as e:
            return render(request, 'error.html', {'error_message': 'Error reading CSV file: ' + str(e)})
        
            # Check if the "reset_session" parameter is in POST data
    # if request.method == 'POST' and 'reset' in request.POST:
    #     request.session.clear()  # Clear the entire session
    #     # return redirect('upload')

    return render(request, 'upload.html')
def upload_file(request):

    
    # Check if the "reset" parameter is in POST data
    if request.method == 'POST' and 'reset' in request.POST:
        # Get the original DataFrame from the session and update the current DataFrame
        json_data = request.session.get('original_data_frame')
        if json_data:
            df = json_to_dataframe(json_data)
            request.session['data_frame'] = dataframe_to_json(df)
        json_geodata = request.session.get('geodata_frame')
        if json_geodata:
            del request.session['geodata_frame']
        pred_df = request.session.get('prediction_dataframe')
        if pred_df:
            del request.session['prediction_dataframe']
                



    # Get DataFrame from session or redirect back to the upload view
    json_data = request.session.get('data_frame')
    if not json_data:
        return redirect('upload')

    df = json_to_dataframe(json_data)
    # ...

    json_geodata = request.session.get('geodata_frame')
    json_pred_data = request.session.get('prediction_dataframe')
    if not json_geodata:
        gdf = None
        preview_geodataframe = preview_dataframe(df, limit=5)
        columns = df.columns.tolist()
        numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])]
        non_numeric_columns = [col for col in columns if not pd.api.types.is_numeric_dtype(df[col])]

    else:
        gdf = json_to_geodataframe(json_geodata)
        preview_geodataframe = preview_dataframe(gdf, limit=5)
        columns = gdf.columns.tolist()
        numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(gdf[col])]
        non_numeric_columns = [col for col in columns if not pd.api.types.is_numeric_dtype(gdf[col])]

    pred_df = pd.DataFrame()
    error_message = ""
    if json_pred_data:
        pred_df = json_to_dataframe(json_pred_data)
        columns = pred_df.columns.tolist()
        numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(pred_df[col])]
        non_numeric_columns = [col for col in columns if not pd.api.types.is_numeric_dtype(pred_df[col])]


    # # Check if the "reset" parameter is in POST data
    # if request.method == 'POST' and 'reset' in request.POST:
    #     print("here")
    #     # request.session.clear()  # Clear the entire session
    #     request.session.pop('data_frame', None)
    #     # del request.session['data_frame']
    #     # return redirect('upload')

    #original dataframe will show at initial level
    # Show the stats at the initial level
    preview_data, num_rows, num_cols, total_nulls, total_notnull, unique_dtypes, df_dtype_info = update_stats(df)


    if request.method == 'POST':
    
        try:
            # data_limit = int(request.POST.get('datalimit', 10))
            # Process different POST requests and modify DataFrame accordingly
            # if 'dropcolumnmenu' in request.POST:
            #     # Drop selected columns
            #     selected_column = request.POST['dropcolumnmenu']
            #     drop_selected_column(df, selected_column)

            if 'fillnullvalues' in request.POST and 'strategy' in request.POST:
                # Handle missing values
                selected_column = request.POST['fillnullvalues']
                selected_strategy = request.POST['strategy']
                if selected_strategy == 'input_constant':
                    selected_strategy = request.POST['strategy_constant']

                if selected_column == 'complete_data':
                    handle_missing_values(df, strategy=selected_strategy)
                else:
                    handle_missing_values(df, strategy=selected_strategy, columns=[selected_column])

            elif 'select-multi-drop-row' in request.POST or 'row_drop_strategy' in request.POST:
                # Drop rows based on conditions
                selected_columns = request.POST.getlist('select-multi-drop-row', None)
                selected_strategy = request.POST.get('row_drop_strategy', None)
                drop_rows(df, how=selected_strategy, subset=selected_columns)

            elif 'select-col-convert-dtype' in request.POST and 'datatype' in request.POST:
                # Convert column data type
                selected_column = request.POST['select-col-convert-dtype']
                selected_column_type = request.POST['datatype']
                df = convert_column_data_type(request, df, column_name=selected_column, new_data_type=selected_column_type)

            elif 'select-lat' in request.POST and 'select-long' in request.POST:
                # Convert coordinate system
                selected_lat = request.POST['select-lat']
                selected_long = request.POST['select-long']
                if 'cord-sys' in request.POST:
                    selected_cordsystem = request.POST['cord-sys']
                    if selected_cordsystem == 'pcs':
                        if 'cord-sys-units' in request.POST:
                            unit_type = request.POST['cord-sys-units']
                            if unit_type == 'feet':
                                try:
                                    df = feet_to_meter(df, easting_col=selected_long, northing_col=selected_lat)
                                except ValueError as e:
                                    messages.error(request, f"Error: {e}")
                                    return HttpResponseRedirect(reverse('preview'))
                            elif unit_type == 'km':
                                try:
                                    df = km_to_meter(df, easting_col=selected_long, northing_col=selected_lat)
                                except ValueError as e:
                                    messages.error(request, f"Error: {e}")
                                    return HttpResponseRedirect(reverse('preview'))
                        df = utm_to_lat_lon(request, df, easting_col=selected_long, northing_col=selected_lat)
                    elif selected_cordsystem == 'gcs':
                        unit_type = request.POST.get('cord-sys-units', None)
                        if unit_type == 'decideg':
                            try:
                                df = convert_dms_to_decimal(request, df, latitude_col=selected_lat, longitude_col=selected_long)
                            except ValueError as e:
                                messages.error(request, f"Error: {e}")
                                return HttpResponseRedirect(reverse('preview'))
                        else:
                            try:
                                df = convert_lat_lon_columns(request, df, latitude_col=selected_lat, longitude_col=selected_long)
                            except ValueError as e:
                                messages.error(request, f"Error: {e}")
                                return HttpResponseRedirect(reverse('preview'))

                if not df[selected_long].dtype == float or not df[selected_lat].dtype == float:
                    messages.error(request, "Error: Latitude, Longitude, Easting, or Northing columns should have float data type [clean coordinates]")
                    return HttpResponseRedirect(reverse('preview'))
                
            #  ==================== forward geocoding ==================
            elif 'select-multi-addr' in request.POST:
                selected_columns = request.POST.getlist('select-multi-addr', None)
                for column in selected_columns:
                    if column  == 'null':
                        messages.error(request, "Error: 'Select columns' is invalid column")
                    
                df = concatenate_and_geocode(request, df, columns_to_concatenate=selected_columns)

            #  ==================== reverse geocoding ==================
            elif 'select-rev-gc-lat' in request.POST and 'select-rev-gc-long' in request.POST:
                selected_rev_lat = request.POST.get('select-rev-gc-lat', None)
                selected_rev_long = request.POST.get('select-rev-gc-long', None)

                df = convert_lat_lng_to_addresses(request, df, lat = selected_rev_lat, long=selected_rev_long)
            
            elif 'select-x' in request.POST and 'select-y' in request.POST:
                selected_x = request.POST.get('select-x', None)
                selected_y = request.POST.get('select-y', None)

                gdf = dataframe_to_Geodataframe(df, selected_x, selected_y)
                request.session['geodata_frame'] = geodataframe_to_json(gdf)

            elif 'K_val' in request.POST and 'select_gi_feature' in request.POST:
                selected_k_val = request.POST.get('k_val', None)
                selected_gi_feature = request.POST.get('select_gi_feature', None)


                # Check if the checkbox is selected in the POST data
                select_star_parameter = request.POST.get('select_star_parameter', False)

                star_parameter = None  # Initialize star_parameter as None


                ## If the checkbox is selected, get the star_parameter value
                if select_star_parameter:
                    star_parameter_str = request.POST.get('star_parameter', None)
                    if star_parameter_str is not None:
                        try:
                            star_parameter = float(star_parameter_str)
                        except (ValueError, TypeError):
                            star_parameter = None

                gdf = Getis_ord_hotspot_Analysis(gdf, selected_k_val, selected_gi_feature, star_parameter, request)
                request.session['geodata_frame'] = geodataframe_to_json(gdf)

            if 'select_date_var_gd' in request.POST and 'select_desired_feature_gd' in request.POST:
                selected_date_feature = request.POST.get('select_date_var_gd', None)
                selected_desired_feature = request.POST.get('select_desired_feature_gd', None)

                # Check if both selected features are not None and not empty strings
                if selected_date_feature and selected_desired_feature:
                    features = [selected_date_feature, selected_desired_feature]
                    

                    # Ensure 'pred_df' exists and is a DataFrame before performing operations
                    if isinstance(pred_df, pd.DataFrame):
                        # Check if the selected features exist in 'pred_df' columns
                        if all(feature in df.columns for feature in features):
                            pred_df = df[features]

                            # Check if 'df' is a DataFrame before attempting a groupby operation
                            if isinstance(df, pd.DataFrame):
                                # Convert the 'date' column to a datetime data type
                                
                                # Convert the 'date' column to a datetime object
                                pred_df = df.groupby([selected_date_feature, selected_desired_feature]).size().reset_index(name='cases')
                                pred_df.drop_duplicates(subset=[selected_date_feature, selected_desired_feature], inplace=True)

                                pred_df[selected_date_feature] = pd.to_datetime(pred_df[selected_date_feature])

                                # pred_df[selected_date_feature] = pd.to_datetime(pred_df[selected_date_feature], unit='s')
                                
                                
                                unique_dates = pd.date_range(start=pred_df[selected_date_feature].min(), end=pred_df[selected_date_feature].max())
                                unique_districts = pred_df[selected_desired_feature].unique()

                                date_district_combinations = pd.MultiIndex.from_product([unique_dates, unique_districts], names=[selected_date_feature, selected_desired_feature])
                                full_df = pd.DataFrame(index=date_district_combinations).reset_index()

                                # Merge this new DataFrame with your original data to fill in missing combinations
                                filled_df = full_df.merge(pred_df, on=[selected_date_feature, selected_desired_feature], how='left')

                                # Fill missing 'cases' with 0 or cumulative sum
                                filled_df['cases'].fillna(0, inplace=True)
                                print(filled_df)

                                # Convert the selected_date_feature column back to the desired date format
                                # pred_df[selected_date_feature] = pred_df[selected_date_feature].dt.strftime('%d-%m-%Y')
                                # pred_df[selected_date_feature] = pd.to_datetime(pred_df[selected_date_feature], format='%d-%m-%Y', errors='coerce')
                                # pred_df = pred_df.dropna(subset=[selected_date_feature])  # Remove rows with invalid date entries

                                # Create a date range for the entire time period
                                # date_range = pd.date_range(start=min(pred_df[selected_date_feature]), end=max(pred_df[selected_date_feature]))
                                # print(min(pred_df[selected_date_feature]), max(pred_df[selected_date_feature]))

                                # # Create a DataFrame to hold the complete time series data
                                # complete_pred_df = pd.DataFrame()
                                #  # Iterate through unique district names and fill in missing dates
                                # for district in pred_df[selected_desired_feature].unique():
                                #     district_data = pred_df[pred_df[selected_desired_feature] == district].set_index(selected_date_feature)
                                #     district_data = district_data.reindex(date_range)
                                #     district_data[selected_desired_feature] = district
                                #     district_data['cases'] = district_data['cases'].fillna(0)  # Fill missing cases with 0
                                #     # district_data['total_cases'] = district_data['total_cases'].fillna(method='ffill')  # Fill missing total_cases using forward fill
                                #     complete_pred_df = pd.concat([complete_pred_df, district_data])

                                # # Reset the index and save the resulting DataFrame
                                # complete_pred_df = complete_pred_df.reset_index()
                                # complete_pred_df = complete_pred_df.rename(columns={'index': selected_date_feature})
                                # print("sadasda", complete_pred_df.shape)
                                # print("complete_pred_df", complete_pred_df.head())
                                # Store the resulting DataFrame in the session variable
                                request.session['prediction_dataframe'] = dataframe_to_json(filled_df)
                            else:
                                # Handle the case where 'df' is not a DataFrame
                                error_message = "The 'df' variable is not a DataFrame."
                                # You can choose to raise an error, log the error, or provide a user-friendly message.
                        else:
                            # Handle the case where one or both selected features don't exist in 'pred_df'
                            error_message = "One or both selected features do not exist in the data."
                            # You can choose to raise an error, log the error, or provide a user-friendly message.
                    else:
                        # Handle the case where 'pred_df' is not a DataFrame
                        error_message = "The 'pred_df' variable is not a DataFrame."
                        # You can choose to raise an error, log the error, or provide a user-friendly message.
                else:
                    # Handle the case where one or both selected features are empty or None
                    error_message = "Please select valid date and desired features."
                    # You can choose to raise an error, log the error, or provide a user-friendly message.

                # If there is an error, you can raise an exception, log it, or show a user-friendly message.
            if error_message:
                raise ValueError(error_message)
                
            if 'save_db' in request.POST:
                print("ahh")
                json_dat = request.session.get('data_frame')
                if json_dat is not None:
                    df = json_to_dataframe(json_dat)
                    uploaded_file_name = request.session.get('uploaded_file_name')
                    save_dataframe_to_database(request, df, uploaded_file_name)

            if 'save_db_hotspot' in request.POST:
                json_geodata = request.session.get('geodata_frame')
                if json_geodata is None:
                    messages.error(request, 'Cannot save empty geodata file')
                else:
                    gdf = json_to_geodataframe(json_geodata)
                    file_name = 'Hotspot_Analysis_File.csv'
                    save_dataframe_to_database(request, gdf, file_name)
                    messages.success(request, 'Saved Successfully')

            
            if 'save_db_prophet' in request.POST:
                json_fb_forecasted = request.session.get('fb_forcasted_df')
                fb_period = request.session.get('forecasted_period_fb', None)
                fb_freq = request.session.get('forecasted_freq_fb', None)
                fb_model = request.session.get('prophet_model', None)

                if json_fb_forecasted is not None and fb_model is not None:
                    fbforecasteddf = json_to_dataframe(json_fb_forecasted)
                    file_name = 'FB_Forecasts_File'
                    selected_filteration = request.session.get('selected_filteration_fb', [])
                    print("fb", selected_filteration)
                    # Define a dictionary to map fb_freq values to mode values
                    freq_to_mode = {
                        'A': 'years',
                        'Q': 'Quarters',
                        'M': 'Months',
                        'W': 'Weeks',
                        'D': 'Days',
                        'H': 'Hours',
                        'T': 'Minutes',
                        'S': 'Seconds',
                        'L': 'Milliseconds',
                        'U': 'Microseconds',
                        'N': 'Nanoseconds',
                    }

                    if fb_period is not None and fb_freq is not None and fb_freq in freq_to_mode:
                        mode = freq_to_mode[fb_freq]
                        f_per = int(fb_period)
                    else:
                        mode = None  
                        f_per = 0

                    save_forecasts_dataframe_to_db(request, fbforecasteddf, file_name, selected_filteration, f_per, mode, fb_model=fb_model)
                    messages.success(request, 'Saved Successfully')
                else:
                    messages.error(request, 'No forecasts to save data')

            if 'save_db_arima' in request.POST:
                json_arima_forecasted = request.session.get('arima_forecasts', None)
                if json_arima_forecasted is not None:
                    arimaforecasteddf = json_to_dataframe(json_arima_forecasted)
                    file_name = 'AR_MA_Forecasts_File'
                    selected_filteration = request.session.get('selected_fileration_arima', [])
                    forecasting_period = request.session.get('arima_forecasting_period')
                    arima_results = request.session.get('arima_result', None)
                    print(arima_results)
                    save_forecasts_dataframe_to_db(request, arimaforecasteddf, file_name, selected_filteration, forecasting_period, arima_model=arima_results)
                    messages.success(request, 'Saved Successfully')
                else:
                    messages.error(request, 'No forecasts to save data')





                


    # Handle the case when 'K_val' and 'select_gi_feature' are not in request.POST

                    
                            # df = star_parameter(request, df, star_parameter_col=selected_star_parameter)
                


            if gdf is not None:
                columns = gdf.columns.tolist()
                numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(gdf[col])]
                non_numeric_columns = [col for col in columns if not pd.api.types.is_numeric_dtype(gdf[col])]

                preview_geodataframe = preview_dataframe(gdf, limit=5)





            # Update the DataFrame in the session
            request.session['data_frame'] = dataframe_to_json(df)
            # df = json_to_dataframe(df)




            # request.session['geodata_frame'] = geodataframe_to_json(gdf)

            # Update the statistics with the modified DataFrame
            preview_data, num_rows, num_cols, total_nulls, total_notnull, unique_dtypes, df_dtype_info = update_stats(df)

            

            #==================== Pre view data limiter customer without Ajax ====================

            # # Get the user-selected number of rows to display
            # if request.POST.get('datalimit') != 'all':
            #     data_limit = int(request.POST.get('datalimit', 10))
            # else:
            #     #show complete data
            #     data_limit = df.shape[0]
                
            # # Limit the number of rows to display
            # preview_data = preview_dataframe(df, limit=data_limit)
            


        except Exception as e:
            return render(request, 'error.html', {'error_message': 'An error occurred: ' + str(e)})
        
    if not pred_df.empty:
        print("pred_df is not empty")
        columns = pred_df.columns.tolist()
        non_numeric_columns = [col for col in columns if not pd.api.types.is_numeric_dtype(pred_df[col])]
        numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(pred_df[col])]

    else:
        columns = df.columns.tolist()    
        non_numeric_columns = [col for col in columns if not pd.api.types.is_numeric_dtype(df[col])]
        numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])]

    # Calculate unique value counts for each column
    unique_value_counts = df.nunique()
    unique_counts_html = unique_value_counts.to_frame(name='Unique Values').to_html(classes='table table-striped')
    


    
    context = {
        'pred_df_columns': columns,
        'gdf': preview_geodataframe,
        'gdf_numeric': numeric_columns,
        'non_numeric_frame': non_numeric_columns,
        'df_info': df_dtype_info,
        'preview_data': preview_data,
        'num_columns': num_cols,
        'num_rows': num_rows,
        'tot_nulls': total_nulls,
        'total_notnull': total_notnull,
        'unique_dtypes': unique_dtypes,
        'messages': messages.get_messages(request),
        'null_col_wise': df.isnull().sum(),
        'nonnull_col_wise': df.notnull().sum(),
        'describe' : df.describe().to_html(classes='table table-striped'),
        'unique' :  unique_counts_html,
    }

    return render(request, 'preview.html', context)



def grouped_data(request):
    if request.method == 'POST':
        pred_df = pd.DataFrame()
        error_message = None
        if 'select_date_var_gd' in request.POST and 'select_desired_feature_gd' in request.POST:
            json_data = request.session.get('data_frame')
            if json_data is None:
                return JsonResponse({'error': 'Unidentified Error! Please Upload Data Again.'})
            else:
                df = json_to_dataframe(json_data)
                selected_date_feature = request.POST.get('select_date_var_gd', None)
                selected_desired_feature = request.POST.get('select_desired_feature_gd', None)
                # Check if both selected features are not None and not empty strings
                if selected_date_feature and selected_desired_feature:
                    features = [selected_date_feature, selected_desired_feature]

                    # Ensure 'pred_df' exists and is a DataFrame before performing operations
                    if isinstance(pred_df, pd.DataFrame):
                        # Check if the selected features exist in 'pred_df' columns
                        if all(feature in df.columns for feature in features):
                            pred_df = df[features]
                            # Check if 'df' is a DataFrame before attempting a groupby operation
                            if isinstance(df, pd.DataFrame):
                                # Convert the 'date' column to a datetime data type

                                # Convert the 'date' column to a datetime object
                                pred_df = df.groupby([selected_date_feature, selected_desired_feature]).size().reset_index(name='cases')
                                pred_df.drop_duplicates(subset=[selected_date_feature, selected_desired_feature], inplace=True)
                                pred_df[selected_date_feature] = pd.to_datetime(pred_df[selected_date_feature])
                                # pred_df[selected_date_feature] = pd.to_datetime(pred_df[selected_date_feature], unit='s')


                                unique_dates = pd.date_range(start=pred_df[selected_date_feature].min(), end=pred_df[selected_date_feature].max())
                                unique_districts = pred_df[selected_desired_feature].unique()
                                date_district_combinations = pd.MultiIndex.from_product([unique_dates, unique_districts], names=[selected_date_feature, selected_desired_feature])
                                full_df = pd.DataFrame(index=date_district_combinations).reset_index()
                                # Merge this new DataFrame with your original data to fill in missing combinations
                                filled_df = full_df.merge(pred_df, on=[selected_date_feature, selected_desired_feature], how='left')
                                # Fill missing 'cases' with 0 or cumulative sum
                                filled_df['cases'].fillna(0, inplace=True)
                                print(filled_df)

                                request.session['prediction_dataframe'] = dataframe_to_json(filled_df)
                            else:
                                # Handle the case where 'df' is not a DataFrame
                                error_message = "The 'df' variable is not a DataFrame."
                                # You can choose to raise an error, log the error, or provide a user-friendly message.
                        else:
                            # Handle the case where one or both selected features don't exist in 'pred_df'
                            error_message = "One or both selected features do not exist in the data."
                            # You can choose to raise an error, log the error, or provide a user-friendly message.
                    else:
                        # Handle the case where 'pred_df' is not a DataFrame
                        error_message = "The 'pred_df' variable is not a DataFrame."
                        # You can choose to raise an error, log the error, or provide a user-friendly message.
                else:
                    # Handle the case where one or both selected features are empty or None
                    error_message = "Please select valid date and desired features."
                    # You can choose to raise an error, log the error, or provide a user-friendly message.

            if error_message:
                return JsonResponse({'error': error_message}, status=400)
            else:
                pred_col_names = filled_df.columns
                pred_col_names = pred_col_names.to_list()
                return JsonResponse({'success': "Process Complete.", 'pred_col_names': pred_col_names}, status=200)
        else:
            return JsonResponse({'error': 'Invalid request'}, status=400)
    else:
        return JsonResponse({'error': 'Bad Request'}, status=400)

def save_data_to_database(request):
    if request.method == 'POST' and 'save_db' in request.POST:
        print("yo")
        json_data = request.session.get('data_frame')
        if json_data is not None:
            df = json_to_dataframe(json_data)
            uploaded_file_name = request.session.get('uploaded_file_name')
            save_dataframe_to_database(request, df, uploaded_file_name)
            response_data = {'message': 'Data saved successfully'}
            return JsonResponse(response_data)
    else:
        response_data = {'error': 'Invalid request'}
        return JsonResponse(response_data, status=400)
    
# I am making ajax call for saving geodata to database and 
def save_geodata_to_database(request):
    if request.method == 'POST' and 'save_db_hotspot' in request.POST:
        json_geodata = request.session.get('geodata_frame')
        if json_geodata is None:
            return JsonResponse({'error': 'Cannot save empty geodata file'})
        else:
            gdf = json_to_geodataframe(json_geodata)
            file_name = 'Hotspot_Analysis_File.csv'
            save_dataframe_to_database(request, gdf, file_name)
            return JsonResponse({'message': 'GeoData saved successfully'})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    

def save_fb_to_database(request):
    if request.method=='POST' and 'save_db_prophet' in request.POST:
        json_fb_forecasted = request.session.get('fb_forcasted_df')
        fb_period = request.session.get('forecasted_period_fb', None)
        fb_freq = request.session.get('forecasted_freq_fb', None)
        fb_model = request.session.get('prophet_model', None)
        if json_fb_forecasted is not None and fb_model is not None:
            fbforecasteddf = json_to_dataframe(json_fb_forecasted)
            file_name = 'FB_Forecasts_File'
            selected_filteration = request.session.get('selected_filteration_fb', [])
            print("fb", selected_filteration)
            # Define a dictionary to map fb_freq values to mode values
            freq_to_mode = {
                'A': 'years',
                'Q': 'Quarters',
                'M': 'Months',
                'W': 'Weeks',
                'D': 'Days',
                'H': 'Hours',
                'T': 'Minutes',
                'S': 'Seconds',
                'L': 'Milliseconds',
                'U': 'Microseconds',
                'N': 'Nanoseconds',
            }
            if fb_period is not None and fb_freq is not None and fb_freq in freq_to_mode:
                mode = freq_to_mode[fb_freq]
                f_per = int(fb_period)
            else:
                mode = None  
                f_per = 0
            save_forecasts_dataframe_to_db(request, fbforecasteddf, file_name, selected_filteration, f_per, mode, fb_model=fb_model)
            # messages.success(request, 'Saved Successfully')
            return JsonResponse({'message': 'Saved Successfully'})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

def save_arima_to_database(request):
    if 'save_db_arima' in request.POST and request.method=='POST':
        json_arima_forecasted = request.session.get('arima_forecasts', None)
        if json_arima_forecasted is not None:
            arimaforecasteddf = json_to_dataframe(json_arima_forecasted)
            file_name = 'AR_MA_Forecasts_File'
            selected_filteration = request.session.get('selected_fileration_arima', [])
            forecasting_period = request.session.get('arima_forecasting_period')
            arima_results = request.session.get('arima_result', None)
            print(arima_results)
            save_forecasts_dataframe_to_db(request, arimaforecasteddf, file_name, selected_filteration, forecasting_period, arima_model=arima_results)
            return JsonResponse({'message': 'Saved Successfully'})

        else:
            return JsonResponse({'error': 'No forecasts to save data'})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    # if 'save_db_hotspot' in request.POST:
                



def Getis_ord_hotspot_Analysis(geodata, selected_k_val=2, selected_gi_feature=None, selected_star_parameter=False, request=None):
    
    if selected_gi_feature is None:
        if request is not None:
            messages.error(request, 'Please Select a valid feature')
        return None
    else:
        geodata[selected_gi_feature] = geodata[selected_gi_feature].astype(float)


    w_knn = weights.KNN.from_dataframe(geodata, k=int(selected_k_val))
    
    print('here:', selected_star_parameter)
    if not selected_star_parameter:
        print('here1:', selected_star_parameter)
        # Calculate K-nearest neighbors (KNN) spatial weights matrix
        w_knn.transform = 'R'  # This will row-standardize the weights
        weights.fill_diagonal(w_knn, w_knn.max_neighbors)  # Set diagonal to max weight
        gi_knn = esda.G_Local(geodata[selected_gi_feature], w_knn, star=False)
    else:
        print('here2:', selected_star_parameter)
        w_knn.transform = 'R'  # This will row-standardize the weights
        weights.fill_diagonal(w_knn, w_knn.max_neighbors)  # Set diagonal to max weight
        gi_knn = esda.G_Local(geodata[selected_gi_feature], w_knn, star=float(selected_star_parameter))
    
    # Calculate p-values for the Gi statistic using KNN weights
    p_values_knn = gi_knn.p_sim

    # Identify significant hotspots and coldspots using KNN weights
    significant_hotspots_knn = (gi_knn.z_sim > 1.96) & (p_values_knn <= 0.05)
    # print(significant_hotspots_knn)
    significant_coldspots_knn = (gi_knn.z_sim < -1.96) & (p_values_knn <= 0.05)

    # Calculate Gi_bins
    num_bins = 7
    gi_bin_values = pd.cut(gi_knn.z_sim, bins=num_bins, labels=range(-3, 4))

    # Create a mapping of Gi_bin values to hotspot analysis labels
    hotspot_analysis_mapping = {
        -3: "Cold Spot with 99% Confidence",
        -2: "Cold Spot with 95% Confidence",
        -1: "Cold Spot with 90% Confidence",
        0: "Not Significant",
        1: "Hot Spot with 90% Confidence",
        2: "Hot Spot with 95% Confidence",
        3: "Hot Spot with 99% Confidence"
    }

    # Identify points that are not significant
    # not_significant = (gi_knn.z_sim >= -1.96) & (gi_knn.z_sim <= 1.96) & (p_values_knn > 0.05)
    
    # Add z-scores, p-values, Gi_bins, and hotspot analysis to the DataFrame
    geodata["z_score"] = gi_knn.z_sim
    geodata["p_value"] = p_values_knn
    geodata["gi_bin"] = gi_bin_values
    geodata["hotspot_analysis"] = geodata["gi_bin"].map(hotspot_analysis_mapping)

    # print(geodata['z_score'].max())
    # geodata.loc[not_significant, "hotspot_analysis"] = "Not Significant"
    
    # Calculate the local Moran's I values
    moran_loc = esda.Moran_Local(gi_knn.z_sim, w_knn, permutations=9999)

    # Create a Moran's Scatterplot with quadrants and labels
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot High-High (HH) Quadrant
    plt.scatter(gi_knn.z_sim[moran_loc.q==1], moran_loc.Is[moran_loc.q==1], color='red', alpha=0.5, label='HH')

    # Plot Low-Low (LL) Quadrant
    plt.scatter(gi_knn.z_sim[moran_loc.q==3], moran_loc.Is[moran_loc.q==3], color='blue', alpha=0.5, label='LL')

    # Plot High-Low (HL) Quadrant
    plt.scatter(gi_knn.z_sim[moran_loc.q==2], moran_loc.Is[moran_loc.q==2], color='green', alpha=0.5, label='HL')

    # Plot Low-High (LH) Quadrant
    plt.scatter(gi_knn.z_sim[moran_loc.q==4], moran_loc.Is[moran_loc.q==4], color='orange', alpha=0.5, label='LH')
    # Add labels and title
    plt.xlabel("Getis-Ord Gi* Z-Score")
    plt.ylabel("Local Moran's I")
    plt.title("Moran's Scatterplot for Getis-Ord Gi* Analysis")
    # Add a dashed reference line
    plt.axhline(0, color="gray", linestyle="--")
    plt.axvline(0, color="gray", linestyle="--")
    # Add a legend
    plt.legend()
    # Save the plot as an image
    img_data = io.BytesIO()
    plt.savefig(img_data, format='png')
    img_data.seek(0)
    # Encode the image data to base64
    base64_img = base64.b64encode(img_data.read()).decode()

    return geodata, base64_img

def facebook_prophet(dataframe, date_col, feature_y, freq, intervals, seasonality, seasonality_prior_scale, changepoint_prior_scale,  district=None, unique_district=None):
    """
    Perform forecasting using Facebook Prophet.

    Parameters:
        - dataframe: pandas DataFrame containing time series data.
        - date_col: Name of the column in the dataframe containing date values.
        - feature_y: Name of the column in the dataframe containing the target variable.
        - district: Optional, specify a district column for forecasting.
        - unique_district: Optional, spedify unique district for forecasts.
        - freq: specify the frequency for the time series data.
        - intervals: specify the number of intervals for forecasting.
        - seasonality: specify the seasonality components.
        - seasonality_prior_scale: specify the extent to which the seasonality model will fit the data.
        - changepoint_prior_scale: specify the extent to which the behavior of the series changes significantly.

    Returns:
        - dataframe: Original dataframe used for forecasting.
        - forecast: Prophet forecast result.
        - observed_range: Tuple with observed date range information.
        - predicted_range: Tuple with predicted date range information.
        - pred_result_fig: Plotly figure for forecast results.
        - forcast_component_fig: Plotly figure for forecast components.
    """
    if district is not None and unique_district is not None and district != '' and unique_district != []:
        # Apply district filter (replace 'district_column' with the actual column name)
        # dataframe = dataframe[dataframe[district] == unique_district]
        dataframe = dataframe[dataframe[district].isin(unique_district)]



    features = [date_col, feature_y]
    dataframe = dataframe[features]

    # Drop rows with any null values
    dataframe = dataframe.dropna()

    # Renaming the columns with respect to the prophet library
    dataframe.columns = ['ds', 'y']

    # Convert date column to pandas datetime
    dataframe['ds'] = pd.to_datetime(dataframe['ds'], unit='ms')
    # if dataframe['ds'].dtype.name == 'datetime64' or dataframe['ds'].dtype.name == 'date':
    #     print('here')
    #     pass
    # else:
    #     dataframe['ds'] = pd.to_datetime(dataframe['ds'])
    #     # dataframe['ds'] = pd.to_datetime(dataframe['ds'], format="mixed", errors='coerce')

    print(dataframe.head(), dataframe.shape)

    # Sort the DataFrame by the 'ds' column in ascending order
    dataframe = dataframe.sort_values(by='ds')

    # Reset index
    dataframe.reset_index(drop=True, inplace=True)
    # print('df length', len(dataframe))

    if seasonality_prior_scale == None or seasonality_prior_scale == '':
        seasonality_prior_scale = 10 #default
    
    if changepoint_prior_scale == None or changepoint_prior_scale == '':
        changepoint_prior_scale = 0.05 #default

    print("seasonality prior scale: ", seasonality_prior_scale)
    print("changepoint prior scale: ", changepoint_prior_scale)

    # Forecasting
    m = Prophet(seasonality_mode=seasonality, seasonality_prior_scale=seasonality_prior_scale, changepoint_prior_scale=changepoint_prior_scale)
    m.fit(dataframe)
    future = m.make_future_dataframe(periods=intervals, freq=freq)
    forecast = m.predict(future)

    # Getting observed and predicted date ranges
    o_first_date = dataframe['ds'].head(1).values[0]
    o_last_date = dataframe['ds'].tail(1).values[0]
    # observed_range = (o_first_date, o_last_date)

    # Convert the observed range to a list of strings
    observed_range = 'Observed range ', str(o_first_date), ' to ', str(o_last_date)


    p_first_date = forecast['ds'].head(1).values[0]
    p_last_date = forecast['ds'].tail(1).values[0]
    # predicted_range = (p_first_date, p_last_date)

    # Convert the predicted range to a list of strings
    predicted_range = '<br> Forecasted range ', str(p_first_date), ' to ', str(p_last_date)

    forecasted_range = observed_range + predicted_range
    # Plotting results
    pred_result_fig = plot_plotly(m, forecast)

    # Plotting components
    forcast_component_fig = plot_components_plotly(m, forecast)


    return dataframe, forecast, forecasted_range, pred_result_fig, forcast_component_fig, m


# Add a function to validate the input against the regex pattern
def validate_input(input_str):
    pattern = r'^(\d+)\s+(seconds|minutes|hours|days|microsecond|milliseconds|nanoseconds)$'
    if input_str is None:
        return True  # Allow None as a valid input
    return re.match(pattern, input_str)

def fbprophet_dignostic(m, horizon, initial, period):

    #cross validation
    if initial is not None and period is not None and horizon is not None:
        df_cv = cross_validation(m, initial=initial, horizon=horizon, period=period)

    #performance metrics
    df_p = performance_metrics(df_cv)

    #plot cross validation metrics
    fig = plot_cross_validation_metric(df_cv, metric='rmse')

    img_data = io.BytesIO()
    fig.savefig(img_data, format='png')
    img_data.seek(0)
    # Encode the image data to base64
    base64_img = base64.b64encode(img_data.read()).decode()

    return df_cv, df_p, base64_img
        


def model_fb_prophet(request):

    try:
        json_geodata = request.session.get('geodata_frame')
        json_data = request.session.get('data_frame')
        prediction_data = request.session.get('prediction_dataframe')
        
        if not json_geodata and not json_data and not prediction_data:
            return JsonResponse({'error': 'DataFrame not found to model. Upload the Data First' })
        
        if prediction_data:
            mdf = json_to_dataframe(prediction_data)
            print(mdf.shape)
        elif json_geodata:
            mdf = json_to_geodataframe(json_geodata)
        else:
            mdf = json_to_dataframe(json_data)

        if request.method == 'POST':
            selected_date_feature = request.POST.get('select-date-column-fb', None)
            selected_district_feature = request.POST.get('select-district-column-fb', None)
            selected_district_feature_value = request.POST.getlist('select-unique-district[]', None)
            selected_forecast_feature = request.POST.get('select-forecast-column-fb', None)
            selected_forecast_freq = request.POST.get('select-forecast-mode-fb', None)
            selected_forecast_period = int(request.POST.get('Enter-forecast-interval-fb', None))
            selected_seasonality_mode = request.POST.get('select-seasonality-mode-fb', None)
            changepoint_prior_scale = request.POST.get('changepoint_prior_scale', None)
            seasonality_prior_scale = request.POST.get('seasonality_prior_scale', None)
            print("here", changepoint_prior_scale, seasonality_prior_scale)
            if selected_district_feature is None:
                dataframe, forecast, forecasted_range, pred_result_fig, forcast_component_fig, m  = facebook_prophet(mdf, selected_date_feature, selected_forecast_feature, selected_forecast_freq, selected_forecast_period, selected_seasonality_mode, seasonality_prior_scale, changepoint_prior_scale, selected_district_feature, selected_district_feature_value)
            else:
                dataframe, forecast, forecasted_range, pred_result_fig, forcast_component_fig, m = facebook_prophet(mdf, selected_date_feature, selected_forecast_feature, selected_forecast_freq, selected_forecast_period, selected_seasonality_mode, seasonality_prior_scale, changepoint_prior_scale, selected_district_feature, selected_district_feature_value)


            # serialized_model = pickle.dumps(m)
            # Serialize the Prophelt model
            serialized_model = pickle.dumps(m)

            # Encode the serialized model in Base64
            encoded_model = base64.b64encode(serialized_model).decode('utf-8')
            request.session['prophet_model'] = encoded_model



            if forecast is not None:
                request.session['fb_forcasted_df'] = dataframe_to_json(forecast)
                forecast_cols = forecast.columns
                forecast_cols = list(forecast_cols) 

            # if selected_district_feature_value == [] or selected_district_feature_value == '':
            #     # selected_district_feature_value = ['Complete Data']
            #     pass

            pred_result_fig.update_layout(
                title_text=f"Forcasted next {selected_forecast_period}{selected_forecast_freq} {selected_forecast_feature} of {selected_district_feature_value}"  
            )

            forcast_component_fig.update_layout(
                title_text=f"Seasonal decomposition with {selected_seasonality_mode} regressor"
            )

            request.session['forecasted_period_fb'] = selected_forecast_period
            request.session['forecasted_freq_fb'] = selected_forecast_freq

            try:
                # Cross-validation
                print("sass", dataframe.shape)
                horizon = request.POST.get('Horizon', None)
                period = request.POST.get('period', None)
                initial = request.POST.get('initial-fbpv', None)

                if all(map(validate_input, [horizon, period, initial])):
                    df_cv, df_p, p_fig = fbprophet_dignostic(m, horizon, initial, period)
                    df_cv_head = df_cv.tail().to_html(classes='table table-bordered table-hover')
                    df_p_tail = df_p.tail().to_html(classes='table table-bordered table-hover')
                    request.session['fb_cv_df'] = dataframe_to_json(df_cv)
                    request.session['fb_p_df'] = dataframe_to_json(df_p) 
                else:
                    return JsonResponse({'error': 'Input should be in terms of (<number> <space> <interval>) e.g., 365 days/minutes/hours/seconds/microsecond/milliseconds/nanoseconds' })
            
            except Exception as e:
                # Handle diagnostic errors (e.g., invalid input)
                return JsonResponse({'error': "An error occurred during cross-validation: " + str(e)})
            
            # print(selected_district_feature_value)
            request.session['selected_filteration_fb'] = selected_district_feature_value
            jsonresponse = {
                'forecasted_range': forecasted_range,
                'pred_result_fig': pred_result_fig.to_json(),
                'df_cv_tail': df_cv_head,
                'df_p_tail': df_p_tail,
                'p_fig': p_fig,
            }

            return JsonResponse({'message': 'Successs', 'prophet_results': jsonresponse})

        else:
            return JsonResponse({'error': 'Invalid request method'})

    except Exception as e:
        return JsonResponse({'error': 'An unexpected error occurred: ' + str(e)})
    
def model_arima_family(request):
    print("here")
    json_geodata = request.session.get('geodata_frame')
    json_data = request.session.get('data_frame')
    prediction_data = request.session.get('prediction_dataframe')

    if not json_geodata and not json_data and not prediction_data:
        return JsonResponse({'error': 'DataFrame not found to model. Upload data first' })
    
    if prediction_data:
        adf = json_to_dataframe(prediction_data)
    elif json_geodata:
        adf = json_to_geodataframe(json_geodata)
    else:
        adf = json_to_dataframe(json_data)

    if request.method == 'POST':

        selected_date_feature = request.POST.get('select-date-column-autoarima', None)
        selected_district_feature = request.POST.get('select-district-column-autoarima', None)
        selected_district_feature_value = request.POST.getlist('autoarima-select-unique-district[]', [])
        selected_forecast_feature = request.POST.get('autoarima-feature-to-forecast', None)
        check_seasonality = request.POST.get('autoarima_seasonality_checkbox', False)
        select_forecasting_interval = int(request.POST.get('forecasting_interval', None))
        start_p = request.POST.get('start_p', None)
        start_P = request.POST.get('start_P', None)
        end_p = request.POST.get('end_p', None)
        end_P = request.POST.get('end_P', None)
        start_q = request.POST.get('start_q', None)
        start_Q = request.POST.get('start_Q', None)
        end_q = request.POST.get('end_q', None)
        end_Q = request.POST.get('end_Q', None)
        d_autoar = request.POST.get('d', None)
        D_autoar = request.POST.get('D', None)
        m_autoar = request.POST.get('m', None)
        print("district column:", selected_district_feature)
        print("district value:", selected_district_feature_value)
        print("forecasting_interval:", select_forecasting_interval)

        print("start_p:", start_p)
        print("end_p:", end_p)
        print('start_q', start_q)
        print("end_q", end_q)

        known_params_seasonality = request.POST.get('know_arima_params_cb_seasonal', False)
        selected_p_value = request.POST.get('Enter-arima_p_val', None)
        selected_q_value = request.POST.get('Enter-arima_q_val', None)
        selected_d_value = request.POST.get('Enter-arima_d_val', None)
        selected_P_value = request.POST.get('Enter-arima_p_val_seasonal', None)
        selected_Q_value = request.POST.get('Enter-arima_q_val_seasonal', None)
        selected_D_value = request.POST.get('Enter-arima_d_val_seasonal', None)
        seasonality_period = request.POST.get('Enter-arima_seasonal_period', None)
        find_best_params_checkbox = request.POST.get('find_best_params_auto_arima_checkbox', False)
        know_params = request.POST.get('know_arima_params_cb', False)
        print("know_arima",know_params)


        model, base64_img, forecast_df, mae, mse, rmse = ARIMA_model(adf, select_forecasting_interval, selected_date_feature, selected_forecast_feature, selected_district_feature, selected_district_feature_value, check_seasonality, know_params,
                selected_p_value, selected_P_value, selected_d_value, selected_q_value, selected_D_value, selected_Q_value, seasonality_period, start_p, end_p, start_q, end_q, start_P, end_P, start_Q, end_Q, m_autoar, d_autoar, D_autoar, known_params_seasonality, find_best_params_checkbox)  
        
        request.session['selected_fileration_arima'] = selected_district_feature_value
        #to store in db
        #this is not a base64 image instead it is a plotly image and have to change its variable name
        request.session['arima_result'] = base64_img


        aic_value = None
        bic_value = None
        hqic_value = None
        num_observations = None 
        
        if model is not None and know_params is not False:
            aic_value = round(model.aic, 3)
            bic_value = round(model.bic, 3)
            hqic_value = round(model.hqic, 3)
            num_observations = model.nobs
            print(aic_value, bic_value, hqic_value, num_observations)
        else:
            aic_value = round(model.aic(), 3)
            bic_value = round(model.bic(), 3)
            hqic_value = round(model.hqic(), 3)
            num_observations = len(adf)
            print(aic_value, bic_value, hqic_value, num_observations)

        fig = model.plot_diagnostics(figsize=(12, 7))
        img_data = io.BytesIO()
        fig.savefig(img_data, format='png')
        img_data.seek(0)
        # Encode the image data to base64
        model_dignostic = base64.b64encode(img_data.read()).decode()
        if forecast_df is not None:
            forecasted_head = forecast_df.head(7).to_html(classes="table table-hover table-bordered")
            request.session['arima_forecasts'] = dataframe_to_json(forecast_df)
        
        request.session['arima_forecasting_period']  = select_forecasting_interval

        arima_response = {
            'AIC': aic_value,
            'BIC': bic_value,
            'HQIC': hqic_value,
            'num_observations': num_observations,
            'arima_fig': base64_img,
            'model_dignostics_fig' : model_dignostic,
            'forecasted_head' : forecasted_head,
            'mae' : round(mae, 3), 
            'mse' : round(mse, 3),
            'rmse' : round(rmse, 3),
        }

        return JsonResponse({'message': 'Successs', 'arima_results': arima_response})
    else:
        return JsonResponse({'error': 'Invalid request method'})
        


def ARIMA_model(dataframe, forecasting_interval, date, target_feature, district=None, district_value=None, SARIMA=False, know=False, p=None, P=None, d=None, q=None, D=None, Q=None, m=None, startp = None, endp = None, startq = None, endq = None, startP=None, endP=None, startQ=None, endQ=None, m_autoar=None, d_autoar=None, D_autoar=None, known_params_seasonality=False, find_best_params_checkbox=False):
    if district is not None and district_value is not None and district != '' and district_value != []:
        dataframe = dataframe[dataframe[district].isin(district_value)]
        print(dataframe)
        print(dataframe.shape)
        print("here1")

    print("here2")


    features = [date, target_feature]
    dataframe = dataframe[features]

    # Drop rows with any null values
    dataframe = dataframe.dropna()

    # Convert the date column to datetime format if it's not already
    dataframe[date] = pd.to_datetime(dataframe[date], unit='ms')
    
    # Sort the DataFrame by the date column
    dataframe = dataframe.sort_values(by=date)
    
    # If you want to reset the index after sorting
    dataframe = dataframe.reset_index(drop=True)
    
    # Set the 'Date' column as the index
    dataframe.set_index(date, inplace=True)
    print("knoww", know)
    if SARIMA == 'auto_arima_seasonality':
        SARIMA = True
    else:
        SARIMA == False
    if know == 'auto_arima_param_known':
        know = True
    else:
        know = False
    if known_params_seasonality == 'auto_arima_param_known':
        known_params_seasonality = True
    else:
        known_params_seasonality = False

    if find_best_params_checkbox == 'find_best_params_auto_arima_checkbox':
        find_best_params_checkbox = True
    else:
        find_best_params_checkbox = False
    print("Sarima", SARIMA)

    if find_best_params_checkbox == True:
        if SARIMA == False:
            print("sarima false")
            if know == False and known_params_seasonality == False:
                print("here3")
                model = auto_arima(dataframe[target_feature], start_p=int(startp), start_q=int(startq), max_p=int(endp), max_q=int(endq), d=int(d_autoar), seasonal=False, trace=True, error_action='ignore')
                model= model.fit(dataframe[target_feature])
                print(model.summary())

                # Extract p, d, and q values
                p_value = model.order[0]
                d_value = model.order[1]
                q_value = model.order[2]
                
            
                forecast, conf_int = model.predict(n_periods=forecasting_interval, return_conf_int=True)

                # Create a date range for the next 15 days starting from the last date in your data
                last_date = dataframe.index[-1]
                date_range = pd.date_range(start=last_date + pd.DateOffset(days=1), periods=forecasting_interval)

                # Create a DataFrame to hold the forecasts and date range
                forecast_df = pd.DataFrame({'Date': date_range, 'Forecast': forecast, 'Lower_CI': conf_int[:, 0], 'Upper_CI': conf_int[:, 1]})
                
                # Create the Plotly figure for the interactive plot
                fig = go.Figure()

                # Add original data as a scatter plot
                fig.add_trace(go.Scatter(x=dataframe.index, y=dataframe[target_feature], mode='lines', name='Original Data'))

                # Add forecast as a line plot
                fig.add_trace(go.Scatter(x=forecast_df['Date'], y=forecast_df['Forecast'], mode='lines', name=f'Forecast', line=dict(color='red')))

                # Add confidence intervals as shaded areas
                fig.add_trace(go.Scatter(x=forecast_df['Date'], y=forecast_df['Lower_CI'], mode='lines', name='Lower CI', fill=None, line=dict(color='pink')))
                fig.add_trace(go.Scatter(x=forecast_df['Date'], y=forecast_df['Upper_CI'], mode='lines', name='Upper CI', fill='tonexty', line=dict(color='pink')))

                # Customize the layout including the p, d, q values and confidence intervals in the legend
                fig.update_layout(
                    xaxis_title='Date',
                    yaxis_title=target_feature,
                    title=f'ARIMA Forecast with Confidence Intervals (p={p_value}, d={d_value}, q={q_value})',
                    legend=dict(x=0, y=1),
                )


                # Show the interactive plot
                base64_img = fig.to_json()
                actual_values = dataframe[target_feature][-forecasting_interval:]

                # Calculate Mean Absolute Error (MAE)
                mae = mean_absolute_error(actual_values, forecast)

                # Calculate Mean Squared Error (MSE)
                mse = mean_squared_error(actual_values, forecast)

                # Calculate Root Mean Squared Error (RMSE)
                rmse = np.sqrt(mse)

                # Print the calculated metrics
                print("Mean Absolute Error (MAE):", mae)
                print("Mean Squared Error (MSE):", mse)
                print("Root Mean Squared Error (RMSE):", rmse)

        elif SARIMA == True:
            print("sarima true")
            if know == False and known_params_seasonality == False:
                print("here5")
                model = auto_arima(dataframe[target_feature], start_p=int(startp), start_q=int(startq), max_p=int(endp), max_q=int(endq), d=int(d_autoar), start_P=int(startP), start_Q=int(startQ), max_P=int(endP), max_Q=int(endQ), m=int(m_autoar), D=int(D_autoar), seasonal=True, trace=True, error_action='ignore')
                model= model.fit(dataframe[target_feature])
                # Extract p, d, q values
                p_value, d_value, q_value = model.order

                # Extract P, D, Q, m values (seasonal components)
                P_value, D_value, Q_value, m_value = model.seasonal_order
                # Generate forecasts for the next days
                forecast, conf_int = model.predict(n_periods=forecasting_interval, return_conf_int=True)

                # Create a date range for the next 15 days starting from the last date in your data
                last_date = dataframe.index[-1]
                date_range = pd.date_range(start=last_date + pd.DateOffset(days=1), periods=forecasting_interval)

                # Create a DataFrame to hold the forecasts and date range
                forecast_df = pd.DataFrame({'Date': date_range, 'Forecast': forecast, 'Lower_CI': conf_int[:, 0], 'Upper_CI': conf_int[:, 1]})
                # Create the Plotly figure for the interactive plot
                fig = go.Figure()

                # Add original data as a scatter plot
                fig.add_trace(go.Scatter(x=dataframe.index, y=dataframe[target_feature], mode='lines', name='Original Data'))

                # Add forecast as a line plot
                fig.add_trace(go.Scatter(x=forecast_df['Date'], y=forecast_df['Forecast'], mode='lines', name='Forecast', line=dict(color='red')))

                # Add confidence intervals as shaded areas
                fig.add_trace(go.Scatter(x=forecast_df['Date'], y=forecast_df['Lower_CI'], mode='lines', name='Lower CI', fill=None, line=dict(color='pink')))
                fig.add_trace(go.Scatter(x=forecast_df['Date'], y=forecast_df['Upper_CI'], mode='lines', name='Upper CI', fill='tonexty', line=dict(color='pink')))

                # Customize the layout
                fig.update_layout(
                    xaxis_title='Date',
                    yaxis_title=target_feature,
                    title=f'SARIMA Forecast with order (p={p_value}, d={d_value}, q={q_value})(P={P_value}, D={D_value}, Q={Q_value}, m={m_value})',
                    legend=dict(x=0, y=1),
                )

                # Show the interactive plot
                base64_img = fig.to_json()
                actual_values = dataframe[target_feature][-forecasting_interval:]
                
                # Calculate Mean Absolute Error (MAE)
                mae = mean_absolute_error(actual_values, forecast)
                
                # Calculate Mean Squared Error (MSE)
                mse = mean_squared_error(actual_values, forecast)
                
                # Calculate Root Mean Squared Error (RMSE)
                rmse = np.sqrt(mse)
                
                # Print the calculated metrics
                print("Mean Absolute Error (MAE):", mae)
                print("Mean Squared Error (MSE):", mse)
                print("Root Mean Squared Error (RMSE):", rmse)
                print(model.summary())

    elif find_best_params_checkbox == False:
        if know == True and known_params_seasonality == False and SARIMA == False:
            print("here4")
            model = ARIMA(dataframe[target_feature], order=(int(p), int(d), int(q)))
            model= model.fit()
            
            # Generate a single-step forecast
            forecast = model.forecast(steps=forecasting_interval)  # Forecast for the next single step

            # Calculate the standard error (stderr) and confidence intervals (conf_int) manually
            stderr = np.std(model.resid)
            z_score = 1.96  # For a 95% confidence interval

            # Calculate confidence intervals for the single-step forecast
            conf_int_lower = forecast - z_score * stderr
            conf_int_upper = forecast + z_score * stderr

            # Create a date range for the next single step
            last_date = dataframe.index[-1]
            date_range = pd.date_range(start=last_date, periods=forecasting_interval)

            # Create a DataFrame to store the single-step forecast and confidence intervals
            forecast_df = pd.DataFrame({
                'Date': date_range,
                'Forecast': forecast,
                'Lower_CI': conf_int_lower,
                'Upper_CI': conf_int_upper
            })

            # Create the Plotly figure for the interactive plot
            fig = px.line(dataframe, x=dataframe.index, y=target_feature, labels={'index': 'Date', target_feature: 'Cases'}, title='ARIMA Single-Step Forecast')
            fig.add_scatter(x=forecast_df['Date'], y=forecast_df['Forecast'], mode='lines', name='Forecast', line=dict(color='red'))
            fig.add_scatter(x=forecast_df['Date'], y=forecast_df['Lower_CI'], mode='lines', name='Lower CI', line=dict(color='pink'))
            fig.add_scatter(x=forecast_df['Date'], y=forecast_df['Upper_CI'], mode='lines', name='Upper CI', fill='tonexty', line=dict(color='pink'))

            # Customize the layout
            fig.update_layout(
                xaxis_title='Date',
                yaxis_title=target_feature,
                title=f'ARIMA Forecast with order (p={p}, d={d}, q={q})',
                legend=dict(x=0, y=1),
            )

            # Show the interactive plot
            base64_img = fig.to_json()
            actual_values = dataframe[target_feature][-forecasting_interval:]
                
            # Calculate Mean Absolute Error (MAE)
            mae = mean_absolute_error(actual_values, forecast)
            
            # Calculate Mean Squared Error (MSE)
            mse = mean_squared_error(actual_values, forecast)
            
            # Calculate Root Mean Squared Error (RMSE)
            rmse = np.sqrt(mse)
            
            # Print the calculated metrics
            print("Mean Absolute Error (MAE):", mae)
            print("Mean Squared Error (MSE):", mse)
            print("Root Mean Squared Error (RMSE):", rmse)
            print(model.summary())

        elif know == True and known_params_seasonality == True and SARIMA == False:
            print("here 6")
            model = sm.tsa.statespace.SARIMAX(dataframe[target_feature], order=(int(p), int(d), int(q)), seasonal_order=(int(P), int(D), int(Q), int(m)))
            model = model.fit()

            # Generate forecasts for the next forecasting_interval days
            forecast = model.get_forecast(steps=forecasting_interval)

           # Extract forecasted values and confidence intervals
            forecast_mean = forecast.predicted_mean
            forecast_conf_int = forecast.conf_int()

            # Create a date range for the next forecasting_interval days starting from the last date in your data
            last_date = dataframe.index[-1]
            date_range = pd.date_range(start=last_date, periods=forecasting_interval)

            # Create a DataFrame to store the forecasted values and date range
            forecast_df = pd.DataFrame({
                'Date': date_range,
                'Forecast': forecast_mean,
                'Lower_CI': forecast_conf_int.iloc[:, 0].values,  # Lower CI column
                'Upper_CI': forecast_conf_int.iloc[:, 1].values   # Upper CI column
            })

            # Create a Plotly figure for the interactive plot
            fig = go.Figure()
            
            # Add original data as a scatter plot
            fig.add_trace(go.Scatter(x=dataframe.index, y=dataframe[target_feature], mode='lines', name='Original Data'))
            
            # Add forecast mean as a line plot
            fig.add_trace(go.Scatter(x=date_range, y=forecast_mean, mode='lines', name='Forecast', line=dict(color='red')))
            
            # Add confidence intervals as shaded areas
            fig.add_trace(go.Scatter(x=date_range, y=forecast_conf_int.iloc[:, 0].values, mode='lines', name='Lower CI', fill=None, line=dict(color='pink')))
            fig.add_trace(go.Scatter(x=date_range, y=forecast_conf_int.iloc[:, 1].values, mode='lines', name='Upper CI', fill='tonexty', line=dict(color='pink')))
            
            # Customize the layout
            fig.update_layout(
                xaxis_title='Date',
                yaxis_title=target_feature,
                title=f'SARIMA Forecast with order (p={p}, d={d}, q={q})(P={P}, D={D}, Q={Q}, m={m})',
                legend=dict(x=0, y=1),
            )

            # Show the interactive plot
            base64_img = fig.to_json()

            actual_values = dataframe[target_feature][-forecasting_interval:]
            # forecast = pd.DataFrame(forecast)
            forecast_values = forecast.predicted_mean
            # Calculate Mean Absolute Error (MAE)
            mae = mean_absolute_error(actual_values, forecast_values)
            
            # Calculate Mean Squared Error (MSE)
            mse = mean_squared_error(actual_values, forecast_values)

            
            # Calculate Root Mean Squared Error (RMSE)
            rmse = np.sqrt(mse)
            
            # Print the calculated metrics
            print("Mean Absolute Error (MAE):", mae)
            print("Mean Squared Error (MSE):", mse)
            print("Root Mean Squared Error (RMSE):", rmse)


    return model, base64_img, forecast_df, mae, mse, rmse

    

#for fb forecasting only    
def fetch_unique_districts(request):
    if request.method == 'POST':
        selected_district_column = request.POST.get('selected_district_column', None)
        print(selected_district_column)
        # Check if a district column was selected
        if selected_district_column is not None:
            json_geodata = request.session.get('geodata_frame')
            json_data = request.session.get('data_frame')
            if not json_geodata and not json_data:
                return JsonResponse({'error': 'GeoDataFrame not found to model' })
    
            if json_geodata:
                mdf = json_to_geodataframe(json_geodata)
            else:
                mdf = json_to_dataframe(json_data)
            print(mdf)
            # Get the unique district values
            unique_districts = mdf[selected_district_column].unique()
            print("unique: ", unique_districts)
            # Return the unique district values as JSON
            return JsonResponse({'unique_districts': list(unique_districts)})

    # Handle invalid or missing data
    return JsonResponse({'error': 'Invalid request or missing data'})



def getis_ord_gi_hotspot_analysis(request):
    json_geodata = request.session.get('geodata_frame')

    if not json_geodata:
        return JsonResponse({'error': 'GeoDataFrame not found'})
    
    gdf = json_to_geodataframe(json_geodata)

    if request.method == 'POST':
        if 'geometry' in gdf.columns and isinstance(gdf['geometry'], gpd.GeoSeries):
            pass
        else:
            return JsonResponse({'error': 'Convert the dataframe into GeoSeries'})
        selected_k_val = request.POST.get('K_val', None)
        selected_gi_feature = request.POST.get('select_gi_feature', None)
        # select_star_parameter = request.POST.get('select_star_parameter', False)
        star_parameter_str = request.POST.get('star_parameter', None)

        # Check if the checkbox is selected in the POST data
        select_star_parameter = request.POST.get('select_star_parameter', False)

        star_parameter = None  # Initialize star_parameter as None

        # If the checkbox is selected, get the star_parameter value
        if select_star_parameter:
            star_parameter_str = request.POST.get('star_parameter', None)
            if star_parameter_str is not None:
                try:
                    star_parameter = float(star_parameter_str)
                except (ValueError, TypeError):
                    star_parameter = None
        # Set a random seed for reproducibility
        # set_random_seed()
        gdf, base64_img = Getis_ord_hotspot_Analysis(gdf, selected_k_val, selected_gi_feature, star_parameter, request)

        request.session['geodata_frame'] = geodataframe_to_json(gdf)
        preview_geodataframe = preview_dataframe(gdf, limit=5)

        stats_column = ['z_score', 'p_value']
        subset_gdf = gdf[stats_column]

        unique_bins = gdf['gi_bin'].unique().tolist()
        # Serialize the list to JSON
        unique_bins_json = json.dumps(unique_bins)
        unique_hotspots = gdf['hotspot_analysis'].unique().tolist()
        unique_hotspots_json = json.dumps(unique_hotspots)

        # Calculate statistics using pandas
        stats = subset_gdf.describe().to_html(classes='table table-hover table-bordered table-striped')

        geodataframe_html = preview_geodataframe.to_html(classes='table table-light fade-out table-bordered') 
        analysis_results = f"Selected K Value: <b>{selected_k_val}</b><br>Selected Feature: <b>{selected_gi_feature}</b></br>Star Parameter: <b>{star_parameter}</b><br>"

        json_response = {
            'analysis_results': analysis_results,
            'geodataframe': geodataframe_html, 
            'stats': stats, 
            'unique_bins': unique_bins_json, 
            'unique_hotspots': unique_hotspots_json,
            # 'graph': graph_json,
            'sangi': base64_img,
        }


        return JsonResponse({'message': 'Getis-ord Gi* calculated successfully!', 'json_response': json_response})
    else:
        return JsonResponse({'error': 'Invalid request method'})

def download_geodata(request):
    geodata = request.session.get('geodata_frame')

    if geodata:
        gdf = json_to_geodataframe(geodata)
        # Parse the JSON data into a DataFrame
        # gdf = pd.read_json(geodata)

        # Convert the DataFrame to CSV format
        geodata = gdf.to_csv(index=False)
        # Create a response with the CSV data as a file attachment
        response = HttpResponse(geodata, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Hotspot Analysis.csv"'
        return response

    return HttpResponse('CSV data not available in the session.')



def preview_data(request):
    json_data = request.session.get('data_frame')
    if not json_data:
        return JsonResponse({'error': 'Data not available'})

    df = json_to_dataframe(json_data)

    selected_limit = int(request.GET.get('limit', default=10))
    paginated_df = df.head(selected_limit)  # Get the DataFrame with the desired limit
    # print(paginated_df)
    # Further preprocessing here (e.g., dropping columns)
    # paginated_df['date'] = pd.to_datetime(paginated_df['date'])

    # Convert the paginated DataFrame to JSON
    paginated_data_json = paginated_df.to_json(orient='records')
    # print(paginated_data_json)

    return JsonResponse({'data': paginated_data_json})

# def generate_hotspot_plot(request):
    
    
#     return JsonResponse({'graph': graph_json})

def convert_to_geodataframe(request):
    try:
        json_data = request.session.get('data_frame')
        if not json_data:
            return JsonResponse({'error': 'GeoDataFrame not found'})
        df = json_to_dataframe(json_data)
        if request.method == 'POST':
            selected_x = request.POST.get('select-x', None)
            selected_y = request.POST.get('select-y', None)

            # Perform the conversion here and save the GeoDataFrame in the session
            gdf = dataframe_to_Geodataframe(df, selected_x, selected_y)
            request.session['geodata_frame'] = geodataframe_to_json(gdf)
            preview_geodataframe = preview_dataframe(gdf, limit=5)

            # Get the column names of the GeoDataFrame
            columns = gdf.columns.tolist()

            # Filter columns based on data types (int or float)
            numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(gdf[col])]

            # Convert the GeoDataFrame to HTML content
            geodataframe_html = preview_geodataframe.to_html(classes='table table-light fade-out table-bordered') 

            return JsonResponse({'message': 'Conversion successful', 'geodataframe': geodataframe_html, 'columns': numeric_columns})
        else:
            return JsonResponse({'error': 'Invalid request method'})
        
    except ValueError as e:
        return JsonResponse({'error': str(e)})

    except Exception as e:
        return JsonResponse({'error': 'An error occurred during conversion. ' + str(e)})
    



    
    

def handle_drop_columns(request):
    if request.method == 'POST':
        selected_column = request.POST.get('column')
        
        # Retrieve the DataFrame from the session
        json_data = request.session.get('data_frame')
        if json_data:
            df = json_to_dataframe(json_data)
            # Drop the selected column
            # df.drop(columns=[selected_column], inplace=True)
            
            # print("Selected: ", selected_column)
            drop_selected_column(df, selected_column)
           # Update the describe DataFrame
            
            # print(describe_df)
            
            # Update the DataFrame and describe DataFrame in the session
            request.session['data_frame'] = dataframe_to_json(df)
            # print(describe_df)
            
            return JsonResponse({'message': f'<b>{selected_column}</b> column dropped successfully', 'data_frame': dataframe_to_json(df)})
        else:
            return JsonResponse({'error': 'Data not available'})

    return JsonResponse({'error': 'Invalid request method'})




            # if 'dropcolumnmenu' in request.POST:
            #     # Drop selected columns
            #     selected_column = request.POST['dropcolumnmenu']
            #     drop_selected_column(df, selected_column)
            # preview_data, num_rows, num_cols, total_nulls, total_notnull, unique_dtypes, df_dtype_info = update_stats(df)


def update_statistics(request):
    if request.method == 'GET':
        json_data = request.session.get('data_frame')
        if json_data:
            df = json_to_dataframe(json_data)
            preview_data, preview_datatypes_html, stats, describe_data, unique_counts_html, null_colwise, nonnull_colwise_html = update_statss(df)

            json_stats_response = {
                'stats': stats,
                'describe_data': describe_data, 
                'unique_dtypes': unique_counts_html,
                'null_colwise': null_colwise,
                'nonull_colwise': nonnull_colwise_html,
                'datatypes': preview_datatypes_html,
            }
            # print(type(preview_data))
            return JsonResponse(json_stats_response)

    return JsonResponse({'error': 'Invalid request method'})


def download_csv(request):
    # Store the CSV data in the session
    # request.session['csv_data'] = csv_file.read().decode('utf-8')

    # Retrieve the CSV data from the session
    csv_data = request.session.get('data_frame')

    if csv_data:
        # Parse the JSON data into a DataFrame
        df = pd.read_json(csv_data)

        # Convert the DataFrame to CSV format
        csv_data = df.to_csv(index=False)
        # Create a response with the CSV data as a file attachment
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="data.csv"'
        return response

    return HttpResponse('CSV data not available.')

def export_fb_forecasted_csv(request):
    # Store the CSV data in the session
    # request.session['csv_data'] = csv_file.read().decode('utf-8')

    # Retrieve the CSV data from the session
    csv_data = request.session.get('fb_forcasted_df')

    if csv_data:
        # Parse the JSON data into a DataFrame
        df = pd.read_json(csv_data)

        # Convert the DataFrame to CSV format
        csv_data = df.to_csv(index=False)
        # Create a response with the CSV data as a file attachment
        response = HttpResponse(csv_data, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="fbprophet_forecasted_results.csv"'
        return response

    return HttpResponse('Forecast data not available in the session to export, clear the cache and try again.')

# Create a function to generate the zip file
def generate_zip(files):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            # 'file' should be a tuple containing file name and its content
            file_name, file_content = file
            zipf.writestr(file_name, file_content)

    return zip_buffer.getvalue()

def export_fb_cv_csv_zip(request):
    # Retrieve the CSV data from the session
    csv__fb_cv_data = request.session.get('fb_cv_df')
    csv__fb_p_data = request.session.get('fb_p_df')
    csv__fb_forecasted_data = request.session.get('fb_forcasted_df')

    if csv__fb_cv_data and csv__fb_p_data:
        # Parse the JSON data into a DataFrame
        fbcv = pd.read_json(csv__fb_cv_data)
        fbp = pd.read_json(csv__fb_p_data)
        fbforecast = pd.read_json(csv__fb_forecasted_data)

        # Convert the DataFrame to CSV format
        csv__fb_cv_data = fbcv.to_csv(index=False)
        csv__fb_p_data = fbp.to_csv(index=False)
        csv__fb_forecasted_data = fbforecast.to_csv(index=False)
    # Prepare a list of files to include in the zip
    csv_files = [
        ("cross validation.csv", csv__fb_cv_data),
        ("performance metrics.csv", csv__fb_p_data),
        ("fbprophet forecasts.csv", csv__fb_forecasted_data),
    ]

    # Generate the zip file
    zip_data = generate_zip(csv_files)

    # Create an HttpResponse with the zip file
    response = HttpResponse(zip_data, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="fbprophet_evaluation.zip"'

    return response

def export_arima_results(request):

    arima_forecasts = request.session['arima_forecasts']

    if arima_forecasts is not None:
        af = pd.read_json(arima_forecasts)

        arima_forecasts = af.to_csv(index=False)

        response = HttpResponse(arima_forecasts, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="forecasted_results.csv"'
        return response

    return HttpResponse('Forecast data not available in the session to export, clear the cache and try again.')


# def handle_change_dtypes(request):
#     if request.method == 'POST':
#         selected_column = request.POST.get('column')
#         selected_dtype = request.POST.get('dtype_to_convert')
#         if selected_column is not None and selected_dtype is not None:



def handle_fill_null_values(request):
    if request.method == 'POST':
        selected_column = request.POST.get('column')
        selected_strategy = request.POST.get('strategy')
        if selected_strategy == 'input_constant':
            selected_strategy = request.POST.get('constant_value')
        
            # print(selected_strategy)

        # Retrieve the DataFrame from the session
        json_data = request.session.get('data_frame')
        if json_data:
            df = json_to_dataframe(json_data)

            if selected_column == 'complete_data':
                # Handle missing values based on the selected strate
                handle_missing_values(df, strategy=selected_strategy)
                # selected_column = 'Complete dataframe'
            else:
                handle_missing_values(df, strategy=selected_strategy, columns=[selected_column])

            # Update the DataFrame in the session
            request.session['data_frame'] = dataframe_to_json(df)

            return JsonResponse({'message': f'<b>{selected_column}</b> null values filled successfully with strategy {selected_strategy}'})
        else:
            return JsonResponse({'error': 'Data not available'})

    return JsonResponse({'error': 'Invalid request method'})



def handle_drop_rows(request):
    if request.method == 'POST':
        selected_columns = request.POST.getlist('select-multi-drop-row[]', None)
        selected_strategy = request.POST.get('row_drop_strategy', None)

        if not selected_columns or not selected_strategy:
            return JsonResponse({'error': 'Invalid input'})

        # Retrieve the DataFrame from the session
        json_data = request.session.get('data_frame')
        if json_data:
            df = json_to_dataframe(json_data)
            drop_rows(df, how=selected_strategy, subset=selected_columns)
            request.session['data_frame'] = dataframe_to_json(df)

            return JsonResponse({'message': 'Rows dropped successfully'})
        else:
            return JsonResponse({'error': 'Data not available'})

    return JsonResponse({'error': 'Invalid request method'})

def handle_data_type_conversion(request):
    try:
        if request.method == 'POST':
            # Extract form data
            selected_column = request.POST.get('select-col-convert-dtype', None)
            selected_column_type = request.POST.get('datatype', None)

            if not selected_column_type or not selected_column:
                raise ValueError('Invalid input')

            # Retrieve the DataFrame from the session
            json_data = request.session.get('data_frame')
            if not json_data:
                raise ValueError('Data not available')

            df = json_to_dataframe(json_data)
            df = convert_column_data_type(request, df, column_name=selected_column, new_data_type=selected_column_type)
            request.session['data_frame'] = dataframe_to_json(df)

            # Return a JSON response indicating success
            return JsonResponse({'message': 'Data type conversion successful'})

    except ValueError as ve:
        return JsonResponse({'error': str(ve)})

    except Exception as e:
        return JsonResponse({'error': 'An unexpected error occurred'})

    # Handle other HTTP methods or invalid requests
    return JsonResponse({'error': 'Invalid request'})


#handle coodrdinates

def handle_coordinate_system_conversion(request):
    try:
        if request.method == 'POST':
            # Extract form data
            selected_lat = request.POST.get('select-lat', None)
            selected_long = request.POST.get('select-long', None)
            selected_cordsystem = request.POST.get('cord-sys', None)

            print(selected_lat, selected_long, selected_cordsystem)
            if not selected_lat or not selected_long or not selected_cordsystem or not selected_lat:
                raise ValueError('Invalid input')
            
            # Retrieve the DataFrame from the session
            json_data = request.session.get('data_frame')
            if not json_data:
                raise ValueError('Data not available')
            df = json_to_dataframe(json_data)
            
            
            if selected_cordsystem == 'pcs':
                unit_type = request.POST['cord-sys-units']
                if unit_type == 'feet':
                    try:
                        df = feet_to_meter(df, easting_col=selected_long, northing_col=selected_lat)
                    except ValueError as e:
                        return JsonResponse({'error': str(e)})
                elif unit_type == 'km':
                    try:
                        df = km_to_meter(df, easting_col=selected_long, northing_col=selected_lat)
                    except ValueError as e:
                        return JsonResponse({'error': str(e)})
                df = utm_to_lat_lon(request, df, easting_col=selected_long, northing_col=selected_lat)
                request.session['data_frame'] = dataframe_to_json(df)

            elif selected_cordsystem == 'gcs':
                print("here")
                unit_type = request.POST.get('cord-sys-units', None)
                print("Unit_type", unit_type)
                if unit_type == 'decideg':
                    try:
                        df = convert_dms_to_decimal(request, df, latitude_col=selected_lat, longitude_col=selected_long)
                        request.session['data_frame'] = dataframe_to_json(df)

                    except ValueError as e:
                        return JsonResponse({'error': str(e)})
                else:
                    try:
                        print("here2")
                        print(df)
                        df = convert_lat_lon_columns(request, df, latitude_col=selected_lat, longitude_col=selected_long)
                        request.session['data_frame'] = dataframe_to_json(df)
                        print(df)
                    except ValueError as e:
                        return JsonResponse({'error': str(e)})
                
                
            # Check data types of latitude and longitude columns
            if not df[selected_long].dtype == float or not df[selected_lat].dtype == float:
                return JsonResponse({'error': "Latitude, Longitude, Easting, or Northing columns should have float data type [clean coordinates]"})
            
            # Return the modified DataFrame as JSON
            return JsonResponse({'message': 'Coordinate system conversion successful'})

    except Exception as e:
        return JsonResponse({'error': 'An unexpected error occurred'})

    # Handle other HTTP methods or invalid requests
    return JsonResponse({'error': 'Invalid request'})

def Logout(request):
    logout(request)
    return redirect('upload')

def Login(request):
    return render(request, "login.html")

def login_user(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        print(email, password)

        # Perform basic input validation
        if not email or not password:
            return JsonResponse({'error': 'Both email and password are required.'})

        # Authenticate the user
        user = authenticate(username=email, password=password)
        print(user)

        if user is not None:
            # Login the user
            login(request, user)
            name = email.split('@')[0]
            request.session['user_name'] = name
            return JsonResponse({'success': 'Login successful!'})
        else:
            return JsonResponse({'error': 'Invalid email or password.'})



def is_valid_password(password):
    # Check if the password meets the specified conditions
    if (8 <= len(password) <= 32) and re.search(r'[A-Z]', password) and re.search(r'[a-z]', password) and re.search(r'[0-9]', password) and re.search(r'[!@#$%_^&*]', password):
        return True
    return False

def is_valid_email(email):
    # Check if the email is valid
    if (
        re.match(r'^[a-zA-Z][a-zA-Z0-9._%+-]{4,}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) and
        not email.isdigit() and
        len(email) >= 5 and
        not re.match(r'^[!@#$%^&*]+$', email) and
        re.match(r'^[a-zA-Z0-9._%+-]+$', email.split('@')[0]) and
        re.match(r'^[a-zA-Z0-9.-]+$', email.split('@')[1])
    ):
        return True
    return False

def register_login(request):
    if request.method == 'POST':
        print("here")
        email = request.POST.get('email')
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')

        # Validate email, password, and check if passwords match
        if not is_valid_email(email):
            return JsonResponse({'error': 'Invalid Email!'})
        
        if not is_valid_password(password):
            return JsonResponse({'error': 'Password must be 8-32 characters long and contain at least one capital letter, one symbol (!@#$%_^&*), and one digit.'})
        
        if password != cpassword:
            return JsonResponse({'error': 'Passwords do not match!'})

        try:
            # Check if the email is already registered
            user = User.objects.get(username=email)
            return JsonResponse({'error': 'Email already exists!'})
        except User.DoesNotExist:
            # Create a new user
            user = User.objects.create_user(username=email, email=email, password=password)
            user.save()
            return JsonResponse({'success': 'Registration successful!'})
        
    return JsonResponse({'error': 'Invalid request method'})

    
def register(request):
    return render(request, 'regiseter.html')


