import json
import pandas as pd
import plotly.express as px
import numpy as np
import geopandas as gpd
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
    request.session.clear()  # Clear the entire session
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
    # ...

    json_geodata = request.session.get('geodata_frame')
    if not json_geodata:
        gdf = None
        preview_geodataframe = preview_dataframe(df, limit=5)
        columns = df.columns.tolist()
        numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])]

    else:
        gdf = json_to_geodataframe(json_geodata)
        preview_geodataframe = preview_dataframe(gdf, limit=5)
        columns = gdf.columns.tolist()
        numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(gdf[col])]






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




    # Handle the case when 'K_val' and 'select_gi_feature' are not in request.POST

                    
                            # df = star_parameter(request, df, star_parameter_col=selected_star_parameter)
                


            







            columns = gdf.columns.tolist()
            numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(gdf[col])]
            # Update the DataFrame in the session
            request.session['data_frame'] = dataframe_to_json(df)
            preview_geodataframe = preview_dataframe(gdf, limit=5)


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
    # Calculate unique value counts for each column
    unique_value_counts = df.nunique()
    unique_counts_html = unique_value_counts.to_frame(name='Unique Values').to_html(classes='table table-striped')

    
    context = {
        'gdf': preview_geodataframe,
        'gdf_numeric': numeric_columns,
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


def Getis_ord_hotspot_Analysis(geodata, selected_k_val=2, selected_gi_feature=None, selected_star_parameter=False, request=None):
    
    if selected_gi_feature is None:
        if request is not None:
            messages.error(request, 'Please Select a valid feature')
        return None
    else:
        geodata[selected_gi_feature] = geodata[selected_gi_feature].astype(float)

    if selected_k_val is None or not isinstance(selected_k_val, int):
        selected_k_val = 2  # Set a default value for selected_k_val if it's None or not an integer
    
    w_knn = weights.KNN.from_dataframe(geodata, k=selected_k_val)

    if not selected_star_parameter:
        # Calculate K-nearest neighbors (KNN) spatial weights matrix
        w_knn.transform = 'R'  # This will row-standardize the weights
        weights.fill_diagonal(w_knn, w_knn.max_neighbors)  # Set diagonal to max weight
        gi_knn = esda.G_Local(geodata[selected_gi_feature], w_knn, star=False)
    else:
        gi_knn = esda.G_Local(geodata[selected_gi_feature], w_knn, star=float(selected_star_parameter))
    
    # Calculate p-values for the Gi statistic using KNN weights
    p_values_knn = gi_knn.p_sim

    # Identify significant hotspots and coldspots using KNN weights
    significant_hotspots_knn = (gi_knn.z_sim > 1.96) & (p_values_knn <= 0.05)
    print(significant_hotspots_knn)
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
    # geodata.loc[not_significant, "hotspot_analysis"] = "Not Significant"

    return geodata



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
            geodataframe_html = preview_geodataframe.to_html(classes='table table-dark fade-out table-bordered') 

            return JsonResponse({'message': 'Conversion successful', 'geodataframe': geodataframe_html, 'columns': numeric_columns})
        else:
            return JsonResponse({'error': 'Invalid request method'})
        
    except ValueError as e:
        return JsonResponse({'error': str(e)})

    except Exception as e:
        return JsonResponse({'error': 'An error occurred during conversion. ' + str(e)})
    


def getis_ord_gi_hotspot_analysis(request):
    json_geodata = request.session.get('geodata_frame')

    if not json_geodata:
        return JsonResponse({'error': 'GeoDataFrame not found'})
    
    gdf = json_to_geodataframe(json_geodata)

    if request.method == 'POST':
        selected_k_val = request.POST.get('K_val', None)
        selected_gi_feature = request.POST.get('select_gi_feature', None)
        select_star_parameter = request.POST.get('select_star_parameter', False)
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
        gdf = Getis_ord_hotspot_Analysis(gdf, selected_k_val, selected_gi_feature, star_parameter, request)
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

        geodataframe_html = preview_geodataframe.to_html(classes='table table-dark fade-out table-bordered') 
        analysis_results = f"Selected K Value: <b>{selected_k_val}</b><br>Selected Feature: <b>{selected_gi_feature}</b></br>Star Parameter: <b>{star_parameter}</b><br>"

        # Load the GeoJSON file
        with open('C:/Users/Ahmer/Downloads/PAK_adm3.json', 'r') as geojson_file:
            data = json.load(geojson_file)

        # Create an empty list to store districts in Punjab
        punjab_districts = []

        # Iterate through the features and filter those in Punjab
        for feature in data['features']:
            if feature['properties']['NAME_1'] == 'Punjab':
                punjab_districts.append(feature)

        # Create a new GeoJSON object with only Punjab districts
        punjab_geojson = {
            'type': 'FeatureCollection',
            'features': punjab_districts
        }
        colors = {
            "Cold Spot with 99% Confidence": "#4475B4",
            "Cold Spot with 95% Confidence": "#849EBA",
            "Cold Spot with 90% Confidence": "#C0CCBE",
            "Not Significant" : "#9C9C9C",
            "Hot Spot with 99% Confidence" : "#D62F27",
            "Hot Spot with 90% Confidence" : "#FAB984",
            "Hot Spot with 95% Confidence" : "#ED7551",
        }
        # Replace gdf, punjab_geojson, colors with your actual data and parameters
        fig = px.choropleth(gdf, geojson=punjab_geojson, color="z_score",
                        locations="pdistrict", featureidkey="properties.NAME_3",
                         color_discrete_map=colors, hover_data=['patient_count'], hover_name='pdistrict', animation_frame='year'
                       )

        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

        # Convert the figure to JSON
        graph_json = fig.to_json()

        json_response = {
            'analysis_results': analysis_results,
            'geodataframe': geodataframe_html, 
            'stats': stats, 
            'unique_bins': unique_bins_json, 
            'unique_hotspots': unique_hotspots_json,
            'graph': graph_json,
        }


        return JsonResponse({'message': 'Getis-ord Gi* calculated successfully!', 'json_response': json_response})
    else:
        return JsonResponse({'error': 'Invalid request method'})
    
    

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

    return HttpResponse('CSV data not available in the session.')


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

#  # Drop rows based on conditions
#                 selected_columns = request.POST.getlist('select-multi-drop-row', None)
#                 selected_strategy = request.POST.get('row_drop_strategy', None)
#                 drop_rows(df, how=selected_strategy, subset=selected_columns)