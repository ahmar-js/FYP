import pandas as pd
import json
import geopandas as gpd

'''
DataFrames are not natively JSON serializable.

converting the DataFrame to a JSON serializable format before storing it in the session 
and convert it back to a DataFrame when retrieving it from the session.

'''

def dataframe_to_json(df):
    return df.to_json(orient='records')

def geodataframe_to_json(gdf):
    return gdf.to_json()


def json_to_geodataframe(json_data):
    return gpd.GeoDataFrame.from_file(json_data)


def json_to_dataframe(json_data):
     data = json.loads(json_data)
     return pd.DataFrame(data)
