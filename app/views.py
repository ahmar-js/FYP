import pandas as pd
import numpy as np
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from .data_preprocessing import read_csv_file, drop_selected_column, handle_missing_values, drop_rows, convert_column_data_type, convert_lat_lon_columns
from .projected_coordinate_systems import utm_to_lat_lon, feet_to_meter, km_to_meter
from .geographical_coordinate_system import convert_dms_to_decimal
from .Geooding import convert_lat_lng_to_addresses, concatenate_and_geocode
from .json_serializable import dataframe_to_json, json_to_dataframe
from django.http import JsonResponse


#================ For custom preview data limiter ================
def preview_dataframe(df, limit=10):
    return df.head(limit)


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
    unique_dtypes = len(df.dtypes.unique())
    df_dtype_info = df.dtypes.apply(lambda x: x.name)  # Convert dtype objects to strings
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
    preview_datatypes_html = preview_datatypes.to_html(classes='table table-dark table-hover table-bordered')


    # df_dtype_info = df_dtype_info.apply(lambda x: int(x) if np.issubdtype(x, np.integer) else x)
    
    stats = {
        'num_rows': str(num_rows),
        'num_cols': str(num_cols),
        'total_nulls': str(total_nulls),
        'total_notnull': str(total_notnull),
    }
    
    
    return preview_data, preview_datatypes_html, stats, describe_data, unique_counts_html, null_colwise_html, nonnull_colwise_html


def upload_view(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        try:
            csv_file = request.FILES['csv_file']
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


    # Get DataFrame from session or redirect back to the upload view
    json_data = request.session.get('data_frame')
    if not json_data:
        return redirect('upload')

    df = json_to_dataframe(json_data)

    # # Check if the "reset" parameter is in POST data
    # if request.method == 'POST' and 'reset' in request.POST:
    #     print("here")
    #     # request.session.clear()  # Clear the entire session
    #     request.session.pop('data_frame', None)
    #     # del request.session['data_frame']
    #     # return redirect('upload')

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

                


            




            # Update the DataFrame in the session
            request.session['data_frame'] = dataframe_to_json(df)

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
    # Calculate unique value counts for each column
    unique_value_counts = df.nunique()
    unique_counts_html = unique_value_counts.to_frame(name='Unique Values').to_html(classes='table table-striped')

    
    context = {
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





def preview_data(request):
    json_data = request.session.get('data_frame')
    if not json_data:
        return JsonResponse({'error': 'Data not available'})

    df = json_to_dataframe(json_data)

    selected_limit = int(request.GET.get('limit', default=10))
    paginated_df = df.head(selected_limit)  # Get the DataFrame with the desired limit

    # Further preprocessing here (e.g., dropping columns)

    # Convert the paginated DataFrame to JSON
    paginated_data_json = paginated_df.to_json(orient='records')

    return JsonResponse({'data': paginated_data_json})

# def describe_data(request):
#     json_data = request.session.get('data_frame')
#     if not json_data:
#         return JsonResponse({'error': 'Data not available to describe'})
#     df = json_to_dataframe(json_data)
#     describe_data = df.describe()
#     describe_data_json = describe_data.to_json(orient='records')
#     print(describe_data_json)
#     print(describe_data)

#     return JsonResponse({'data': describe_data.to_html(classes='table table-bordered table-striped table-')})

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


