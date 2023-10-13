import base64
import colorsys
from datetime import datetime
import pickle
import joblib
import plotly
import plotly.graph_objs as go
from prophet.plot import plot_plotly, plot_components_plotly
import plotly.offline as offline
from plotly.graph_objs import *
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import json
import plotly.express as px
import json
import random
from django.contrib import messages
import os
from django.core.files import File
from django.conf import settings
from django.db.models import Q
import geopandas as gpd
from django.contrib.sessions.models import Session
from shapely.geometry import shape, Point
import matplotlib.pyplot as plt
import random
import matplotlib.patches as mpatches
import branca
import colorsys
import json
import folium
from cartopy import crs as ccrs
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

@login_required(login_url='/Login/')
def home(request):
    uploaded_frame = Uploaded_DataFrame.objects.filter(user=request.user)
    

    m = folium.Map(location=[30.3753,  69.3451], zoom_start=5)
    selected_gdf = None
    selected_df= None
    if request.method == 'POST':
        print("check3")
        selected_X = request.POST.get('conf_select_x', None)
        selected_Y = request.POST.get('conf_select_y', None)
        filtered = request.POST.get('select_filtered_col', None)
        color = request.POST.get('select_color_col', None)
        location = request.POST.get('select_location_col', None)
        hover_data = request.POST.get('select_hover_data_col', None)
        date = request.POST.get('select_date', None)
        size = request.POST.get('select_size', None)
        selected_df_id = request.session.get('selected_dataset_id', None)
        selected_gdf_id = request.session.get('selected_geodataset_id', None)

        if selected_gdf_id is None:
            selected_df = Uploaded_DataFrame.objects.get(id=selected_df_id)
        else:
            selected_gdf = geoDataFrame.objects.get(id=selected_gdf_id)
            selected_df = Uploaded_DataFrame.objects.get(id=selected_df_id)

        if 'selected_dataset_id' in request.session and 'selected_geodataset_id' in request.session:
            del request.session['selected_dataset_id']
            del request.session['selected_geodataset_id']
        else:
            del request.session['selected_dataset_id']


        save_columns_to_database(selected_gdf, selected_df, selected_X, selected_Y, filtered, location, hover_data, date, size, color)
        
    
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
        #because of the FK in dashboard config
        selected_geo_id = request.POST.get('Select_geodataframe', None) #it will be None here
        request.session['selected_dataset_id'] = selected_dataset_id #for saving record to database (home view)
        request.session['selected_dataset_id_preview'] = selected_dataset_id #for retrieve columns (retrieve column names view)


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

        
        # retrieve_column_names(selected_dataset_id, selected_geo_id, geodata_check) #selected_geo_id will be None
        
        # Retrieve associated geodataframe columns 
        uploaded_gdf = geoDataFrame.objects.filter(U_df_id=selected_dataset_id)


        # Retrieve model results based on the selected dataset
        selected_fb_results = fbProphet_forecasts.objects.filter(U_df_id=selected_dataset_id)
        selected_arima_results = ARIMA_forecasts.objects.filter(U_df_id=selected_dataset_id)

        total_arima_record = selected_arima_results.count()
        total_fb_record = selected_fb_results.count()
        total_uploaded_gdf = uploaded_gdf.count()
        total_rec = total_arima_record + total_fb_record


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
            'total_rec': total_rec,
            'total_hs_rec': total_uploaded_gdf,
        }

        return JsonResponse({'message': 'Successs', 'json_response': json_response})
    

    # Handle other HTTP methods or invalid requests
    return JsonResponse({'error': 'Invalid request'})


def get_prophet_results(request):
    if request.method == 'POST':
        selected_dataset_id = request.POST.get('selectedDatasetId', None)
        selected_prophet_result = request.POST.get('selectedPresult', None)

        selected_fb_results = fbProphet_forecasts.objects.get(id=selected_prophet_result)
        forecast_url = selected_fb_results.file.url
        if forecast_url:
            data = pd.read_csv('../FYP'+forecast_url)
            forecast = pd.DataFrame(data)
        

        # Deserialize the model
        # deserialized_model = pickle.loads(selected_fb_results.model)
        # prophelt_model = pickle.loads(selected_fb_results.model)
        serialized_model = base64.b64decode(selected_fb_results.model.encode('utf-8'))
        # Deserialize the model
        prophelt_model = pickle.loads(serialized_model)


        print(type(prophelt_model))
        fig = plot_plotly(prophelt_model, forecast)

        json_response_fb = {
            'fb': "ahmer",
            'fb_plot': fig.to_json(),
            'predictions': len(forecast),

        }

        return JsonResponse({'message': 'Success', 'json_response_fb': json_response_fb})


def get_arima_results(request):
    if request.method == 'POST':
        selected_dataset_id = request.POST.get('selectedDatasetId', None)
        selected_arima_result = request.POST.get('selectedPresult', None)
        selected_arima_results = ARIMA_forecasts.objects.get(id=selected_arima_result)
        fig_arima =selected_arima_results.plot_arima
        forecast_arima_url = selected_arima_results.file.url
        if forecast_arima_url:
           data = pd.read_csv('../FYP'+forecast_arima_url)
           forecast = pd.DataFrame(data)
           print("arima here")
        json_response_arima = {
            'arimaplot':fig_arima,
            'predictions': len(forecast),
        }

        return JsonResponse({'message': 'Success', 'json_response_arima': json_response_arima})
        
        





def Geodatafileselection(request):

    geodata_check = True
    if request.method == 'POST':
        selected_geo_id = request.POST.get('Select_geodataframe', None)
        selected_dataset_id = request.session.get('selected_dataset_id_preview', None)


        request.session['selected_geodataset_id'] = selected_geo_id # save record to database (Home View)

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
        # retrieve_column_names(selected_dataset_id, selected_geo_id, geodata_check)

        json_response = {
            'numeric_columns': numeric_columns,
            'gdf_columns': columns,
            'gdataframe': preview_dataframe(df, limit=50).to_html(classes='table fade-out align-items-center table-flush'),
            'gdf_rows': df_rows,
        }

        return JsonResponse({'message': 'Successs', 'json_response': json_response})
    

    # Handle other HTTP methods or invalid requests
    return JsonResponse({'error': 'Invalid request'})
        


def bin_date_data(data, date_column, bin_by='year'):
    """
    Convert date data to appropriate data type and create bins based on month or year.

    Parameters:
        data (pd.DataFrame): Input DataFrame.
        date_column (str): Name of the column containing date data.
        bin_by (str): Binning option. Options: 'month' or 'year'. Default is 'year'.

    Returns:
        pd.DataFrame: DataFrame with date data converted to appropriate data type and bins created.
    """
    data[date_column] = pd.to_datetime(data[date_column])

    if bin_by == 'month':
        data['month_bin'] = data[date_column].dt.to_period('M')
    elif bin_by == 'year':
        data['year_bin'] = data[date_column].dt.to_period('Y')

    return data

def generate_dark_random_colors(num_colors):
    colors = []
    while len(colors) < num_colors:
        # Generate random HSL color with fixed saturation and lightness (to get darker colors)
        h = random.randint(0, 360)
        s = 80  # Fixed saturation
        l = random.randint(30, 50)  # Restricted lightness for darker colors

        # Convert HSL to RGB
        r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)

        # Convert RGB to hex color code
        color = "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))

        if color not in colors:
            colors.append(color)

    # Randomly shuffle the colors to get unique and random colors
    random.shuffle(colors)
    return colors

def format_popup_content(lat, lon, district, hover_data, size, dt_bin):
    popup_content = f"""
    <div style="font-family: Arial, sans-serif;">
        <h2 style="margin-bottom: 5px; text-align: center;">{hover_data}</h2>
        <table style="width: 100%;">
            <tr>
                <td style="font-weight: bold;">filtered:</td>
                <td>{district}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">size:</td>
                <td>{size}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Bin: </td>
                <td>{dt_bin}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">latitude: </td>
                <td>{lat}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">longitude: </td>
                <td>{lon}</td>
            </tr>
        </table>
    </div>
    """
    return folium.Popup(folium.Html(popup_content, script=True), max_width=300)
def generate_folium_map(df, lat_col, date_column, long_col, filtered_col, hover_data, size):
    df = bin_date_data(df, date_column, bin_by='year')
    # m = folium.Map(location=[30.3753, 69.3451], zoom_start=5)

    # for index, row in df.iterrows():
    #     lat = row[lat_col]
    #     long = row[long_col]
    #     district = row[filtered_col]

    #     folium.CircleMarker(
    #         location=[lat, long],
    #         popup=district,
    #         radius=5,
    #         color='blue',
    #         fill=True,
    #         fill_color='blue'
    #     ).add_to(m)

    # return m._repr_html_()
    # Convert the latitude and longitude columns to Point geometries
    geometry = [Point(xy) for xy in zip(df[long_col], df[lat_col])]

    # Create a GeoDataFrame from the data
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4326", geometry=geometry)

    # Load the world map data
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    # Extract the geometry of Pakistan
    pakistan = world[(world.name == "Pakistan")]['geometry'].iloc[0]


    # Filter out points that lie outside the boundary of Pakistan
    gdf = gdf[gdf['geometry'].within(pakistan)]

    # Create the Folium map centered around Pakistan
    m = folium.Map(location=[gdf['geometry'].centroid.y.mean(), gdf['geometry'].centroid.x.mean()], zoom_start=5, prefer_canvas=False, scrollWheelZoom=False)

    bordersStyle = {"color": 'green', 'weight': 2, 'fillOpacity': 0}

    bordersLayer = folium.GeoJson(
    data="visualization/data/pak_borders/PAK_adm1.json",
    name="Borders",
    style_function=lambda x: bordersStyle)
    bordersLayer.add_to(m)

    # Create unique layers for each patient district and date_bin
    unique_districts = gdf[filtered_col].unique()
    district_layers = {district: folium.FeatureGroup(name=district, show=False) for district in unique_districts}

    unique_date_bins = gdf['year_bin'].unique()
    d_bin = 'year_bin' #For Iteration

    date_bin_layer = {date_bin: folium.FeatureGroup(name=str(date_bin), show=False) for date_bin in unique_date_bins}



    # Generate random dark colors for each unique patient district and date_bin
    district_colors = generate_dark_random_colors(len(unique_districts))
    date_bin_colors = generate_dark_random_colors(len(unique_date_bins))
    color_mapping_district = {district: color for district, color in zip(unique_districts, district_colors)}
    color_mapping_date_bin = {date_bin: color for date_bin, color in zip(unique_date_bins, date_bin_colors)}




    # Add the data points of each patient district and date_bin to the corresponding layer with the respective color
    for index, row in gdf.iterrows():
        lat, lon, district, hover_dat, siz, dt_bin = row[lat_col], row[long_col], row[filtered_col], row[hover_data], row[size], row[d_bin]
        district_color = color_mapping_district[district]
        date_bin_color = color_mapping_date_bin[dt_bin]
        # popup = format_popup_content(lat, lon, district, hover_dat, siz, dt_bin)
        
        # popUpStr = 'Area - {0}<br>District - {1}<br>Province '.format(district, province)
        # iframe = folium.branca.element.IFrame(html=html, width=500, height=300)
        # popup = folium.Popup(iframe, max_width=2650, parse_html=True)
        # test = folium.Html('<b>nm<br>desc</b>', script=True) # i'm assuming this bit runs fine
        # iframe = branca.element.IFrame(html=test, width=350, height=150)
        # popup = folium.Popup(iframe, parse_html=True)

        # popupt = f"District: {district}<br>Province: {province}<br>Longitude: {lon}"

        folium.Circle([lat, lon], radius=2, color=district_color, opacity=0.8, fill_color=district_color).add_to(district_layers[district])

        folium.CircleMarker([lat, lon], radius=4, color=date_bin_color, opacity=0.7, fill=False).add_to(date_bin_layer[dt_bin])


    # Add each patient district's layer to the map
    for district, layer in district_layers.items():
        layer.add_to(m)

    # Add each bin layer to the map
    for d_bin, layer in date_bin_layer.items():
        layer.add_to(m)

    # Add a LayerControl to the map to toggle the patient district and year_bin layers on/off
    folium.LayerControl(collapsed=False).add_to(m)

    # Add legends with small color dots overlaying the map
    for district, color in color_mapping_district.items():
        legend_html = f'<div style="display:inline-block; margin-right:10px; background-color:{color}; height:10px; width:10px;"></div>{district}'
        m.get_root().html.add_child(folium.Element(legend_html))

    # Add legends with small color dots overlaying the map
    for d_bin, color in color_mapping_date_bin.items():
        legend_html = f'<div style="display:inline-block; margin-right:10px; background-color:{color}; height:10px; width:10px;"></div>{d_bin}'
        m.get_root().html.add_child(folium.Element(legend_html))

    return gdf, m._repr_html_()


def generate_plotly_3d_scatter(long, lat, filtered, hover_data, gdf, size, date, color):
    gdf['date_ym'] = pd.to_datetime(gdf[date]).dt.strftime('%Y-%m')
    gdf = gdf.sort_values(by='date_ym')
    # Reset the index while keeping the original index as a new column
    gdf.reset_index(inplace=True, drop=True)
    fig_3d = px.scatter_3d(gdf,
                        x=long,
                        y=lat,
                        z='date_ym',
                        color=color,
                        hover_name=hover_data,
                        hover_data=['patient_count'],
                    # range_color=(-3, 3),
                    # color_discrete_map=colors,
                    # animation_frame="weeks",
                    size_max = 1,
                    height=650,
                    width=900,
                    title="")
    fig_3d.update_layout(font=dict(color="gray"))
    # Set the legend position to the top-left corner
    # Set the legend position to the top-left corner as absolute
    # fig_3d.update_layout(legend=dict(x=0, y=1))
    fig_3d.update_layout(margin={"r":2,"t":2,"l":1,"b":5})
    return fig_3d

def generate_plotly_chloropeth(long, lat, filtered, hover_data, gdf, size, date, color):
    pk_states=json.load(open(r"visualization/data/pak_districts/pakistan_districts.geojson",'r'))
    pk_states['features'][5]['properties']
    district_id_map={}
    for feature in pk_states['features']:
        feature['id'] = feature['properties']['cartodb_id']
        district_id_map[feature['properties']['districts']] = feature['id']
    gdf['District']=gdf[filtered].apply(lambda x:x.title())
    gdf['id_']=gdf['District'].apply(lambda x: district_id_map[x])
    fig_check = px.choropleth_mapbox(gdf,
                    locations='id_',
                    geojson=pk_states,
                    color=color,
                    hover_name="District",
                    hover_data=[hover_data],
                    mapbox_style="carto-positron",
                    center={'lat':31,'lon':72},
                    zoom=4,
                    # range_color=(-4, 4),
                    # color_discrete_map=colors,
                    color_continuous_scale=["blue","#9c9c9c","red" ],
                    animation_frame="date_ym",
                    # title="Analysis on 5 Neighbors",
                    opacity=1)
    return fig_check

#for df only
def retrieve_column_names_df(request):
    selected_dataset_id = request.GET.get('selected_dataset_id')
    geodata_check = request.GET.get('geodata_check', False)
    geodata_check = geodata_check.lower() == 'true'
    select_map = request.GET.get('select_map', False)
    if not geodata_check:
        column_record = ConfigDashboard.objects.get(Q(U_df=selected_dataset_id) & Q(U_gdf__isnull=True))
    selected_dataset = Uploaded_DataFrame.objects.get(id=selected_dataset_id)
    if column_record is not None:
        long = column_record.longitude
        lat = column_record.latitude
        filtered = column_record.filtered
        date = column_record.date
        hover_data = column_record.hover_data
        size = column_record.size

        # dataframe must be selected
        selected_df_url = selected_dataset.file.url
        if selected_df_url:
            data = pd.read_csv('../FYP' + selected_df_url)
            df = pd.DataFrame(data)
            if select_map == 'intensity':
                print("intensity")
                df, map_html = generate_intensity_map(df, lat, date, long, filtered, hover_data, size)
                json_response = {
                    "imap": map_html,
                }
            else:
                df, map_html = generate_folium_map(df, lat, date, long, filtered, hover_data, size)
                json_response = {
                    "dmap": map_html,
                }

            return JsonResponse({'message': 'success', 'json_response': json_response})
    else:
            return JsonResponse({'message': 'error', 'error': 'Selected DataFrame URL not found'})


def generate_intensity_map(df, lat, date, long, filtered, hover_data, size):
    # Load the dataset
    data = df
    
    # Group the data by 'pdistrict' and calculate the sum of 'patient_count' for each district
    district_patient_counts = data.groupby(filtered)[hover_data].sum()
    
    # Determine the district with the highest patient_count
    highest_patient_district = district_patient_counts.idxmax()
    
    # Create a Folium map
    district_map = folium.Map(location=[data[lat].mean(), data[long].mean()], zoom_start=7)
    
    # Iterate through each district and add CircleMarker to the map
    for district, patient_count in district_patient_counts.items():
        intensity = (patient_count / district_patient_counts[highest_patient_district]) * 30  # Scale intensity
        if intensity >= 30:
            colori='red'
        elif intensity < 30 and intensity >= 15:
            colori='blue'
        else:
            colori='green'
        popup_text = f"District: {district}<br>Patient Count: {patient_count}"
    
        iframe = folium.IFrame(popup_text)
        popup = folium.Popup(iframe, min_width=250, max_width=250)
    
        folium.CircleMarker(
            location=[data[data[filtered] == district][lat].iloc[0],
                      data[data[filtered] == district][long].iloc[0]],
            radius=intensity,
            color=colori,
            fill=True,
            fill_color=colori,
            fill_opacity=0.6,
            popup=popup
        ).add_to(district_map)

    return data, district_map._repr_html_()
#for df and gdf
def retrieve_column_names(request):
    selected_dataset_id = request.GET.get('selected_dataset_idd')
    selected_geo_id = request.GET.get('selected_geo_idd')
    geodata_check = request.GET.get('geodata_checkk', False)
    geodata_check = geodata_check.lower() == 'true'
    selecthp_timely = request.GET.get('select_hp_timely_mode', None)
    # date_column = request.GET.get('date_column')
    selected_geodataset = None
    try:
        if not geodata_check:
            column_record = ConfigDashboard.objects.get(Q(U_df=selected_dataset_id) & Q(U_gdf__isnull=True))
        else:
            column_record = ConfigDashboard.objects.get(U_df=selected_dataset_id, U_gdf=selected_geo_id)
            selected_geodataset = geoDataFrame.objects.get(id=selected_geo_id)

        selected_dataset = Uploaded_DataFrame.objects.get(id=selected_dataset_id)
    except ConfigDashboard.DoesNotExist:
        column_record = None

    if column_record is not None:
        long = column_record.longitude
        lat = column_record.latitude
        filtered = column_record.filtered
        date = column_record.date
        hover_data = column_record.hover_data
        size = column_record.size
        color = column_record.color

            #when hotspot dataframe is selected
        if selected_geodataset is not None:
            print("ahmer aamir")
            selected_gdf_url = selected_geodataset.file.url
            if selected_gdf_url:
                data = pd.read_csv('../FYP' + selected_gdf_url)
                gdf = pd.DataFrame(data)
                fig = generate_plotly_3d_scatter(long, lat, filtered, hover_data, gdf, size, date, color)
                if selecthp_timely == 'scatter':
                    plotly_chloro_fig = generateBubbleScatter(long, lat, filtered, hover_data, gdf, size, date, color)
                    json_response = {
                        'fig':fig.to_json(),
                        'plotly_chloro_fig_scatter':plotly_chloro_fig.to_json(),
                    }
                else:
                    plotly_chloro_fig = generate_plotly_chloropeth(long, lat, filtered, hover_data, gdf, size, date, color)
                    json_response = {
                        'fig':fig.to_json(),
                        'plotly_chloro_fig_chloro':plotly_chloro_fig.to_json(),
                    }


            else:
                return JsonResponse({'message': 'error', 'error': 'Selected GeoDataFrame URL not found'})


                

            return JsonResponse({'message': 'success', 'json_response': json_response})
        


    else:
        return JsonResponse({'message': 'error', 'error': 'ConfigDashboard record not found.'})


    
def generateBubbleScatter(long, lat, filtered, hover_data, gdf, size, date, color):
    gdf['date_ym'] = pd.to_datetime(gdf[date]).dt.strftime('%Y-%m')
    gdf = gdf.sort_values(by='date_ym')
    fig = px.scatter(gdf, x=long, y=lat, animation_frame="date_ym", animation_group=filtered,
            size=size, color=color, hover_name=filtered,
            log_x=True, size_max=55, range_x=[10,1000], range_y=[10,90])
    
    return fig


    

    
def save_columns_to_database(selected_gdf_instance, selected_df_instance, selected_X, selected_Y, filtered, location, hover_data, date, size, color):
    # Query the database to check if a record with the same instances exists
    existing_record = ConfigDashboard.objects.filter(Q(U_df=selected_df_instance) & Q(U_gdf=selected_gdf_instance)).first()
    # print("existing record: ", existing_record)
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
            U_gdf=selected_gdf_instance,
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

    # if model_name == geoDataFrame:
    #    # Set the U_df to the ID of the last record in Uploaded_DataFrame
    #    last_uploaded_df = Uploaded_DataFrame.objects.latest('id')
    #    my_file_instance.U_df = last_uploaded_df
    
    # my_file_instance.save()

    if model_name == geoDataFrame:
    # Get the current session ID
        session_key = request.session.session_key

        # Check if the session key is available
        if session_key:
            # Get or create a session object
            session = Session.objects.get(session_key=session_key)

            # Get the last uploaded record's ID from the session data
            last_uploaded_id = session.get('last_uploaded_id')

            if last_uploaded_id:
                # Get the last uploaded record based on the stored ID
                last_uploaded_df = Uploaded_DataFrame.objects.get(id=last_uploaded_id)
                my_file_instance.U_df = last_uploaded_df

    my_file_instance.save()
    
    # Update the session data with the new last uploaded ID
    session['last_uploaded_id'] = my_file_instance.U_df.id
    session.save()

    return HttpResponse("CSV file uploaded to the database successfully.")

def save_forecasts_dataframe_to_db(request, df, name, filtered_by_val=[], period=None, freq=None, fb_model=None, arima_model=None):
    # Generate a timestamp to append to the filename
    # timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filtered_by_val = str(filtered_by_val)  # Convert to JSON string
    if filtered_by_val == '[]':
        filtered_by_val = 'Unfiltered'
    file_name = name + '_' + filtered_by_val + '.csv'
    print("save: ", arima_model)


    if name == 'FB_Forecasts_File':
        model_name = fbProphet_forecasts
        if freq is not None and period is not None:
            my_file_instance = model_name(filtered_by=filtered_by_val, period=period, frequency=freq, model = fb_model)

    else:
        model_name = ARIMA_forecasts
        if period is not None and arima_model is not None:
            my_file_instance = model_name(filtered_by=filtered_by_val, period=period, plot_arima = arima_model)


    

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

    if request.session.get('fb_forcasted_df'):
        del request.session['fb_forcasted_df']
    if request.session.get('prophet_model'):
        del request.session['prophet_model']
    if request.session.get('forecasted_freq_fb'):
        del request.session['forecasted_freq_fb']
    if request.session.get('forecasted_period_fb'):
        del request.session['forecasted_period_fb']
    if request.session.get('fb_cv_df'):
        del request.session['fb_cv_df']
    if request.session.get('fb_p_df'):
        del request.session['fb_p_df']
    if request.session.get('selected_filteration_fb'):
        del request.session['selected_filteration_fb']

    return HttpResponse("CSV file uploaded to the database successfully.")

       