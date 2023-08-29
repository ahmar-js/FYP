import pyproj
from django.contrib import messages


#  ============================= Convert simple GCS to UTM lat longs =============================

# def lat_lon_to_utm(dataframe, latitude_column, longitude_column):
#     # Define the source and target coordinate reference systems (CRS)
#     source_crs = pyproj.CRS("EPSG:4326")  # WGS 84 (latitude-longitude)
#     target_crs = pyproj.CRS("EPSG:24312") # WGS 84 / UTM zone 42N

#     # Create a PyProj Transformer to perform the coordinate transformation
#     transformer = pyproj.Transformer.from_crs(source_crs, target_crs, always_xy=True)

#     # Perform the transformation on the specified columns
#     easting, northing = transformer.transform(dataframe[longitude_column], dataframe[latitude_column])

#     # Add the transformed coordinates as new columns to the DataFrame
#     dataframe['UTM_Easting'] = easting
#     dataframe['UTM_Northing'] = northing

#     return dataframe


#  ============================= Convert UTM coordinates to simple GCS lat longs =============================

# Function to convert UTM coordinates to lat/long coordinates
def utm_to_lat_lon(request, dataframe, easting_col, northing_col):
    # Define the source and target coordinate reference systems (CRS)
    source_crs = pyproj.CRS("EPSG:24312")  # WGS 84 / UTM zone 42N - Kalianpur 1962
    target_crs = pyproj.CRS("EPSG:4326")  # WGS 84 (latitude-longitude)

    # Create a PyProj Transformer to perform the coordinate transformation
    transformer = pyproj.Transformer.from_crs(source_crs, target_crs, always_xy=True)

    try:
        # Perform the transformation
        longitude, latitude = transformer.transform(dataframe[easting_col], dataframe[northing_col])

        # Add new columns to dataframe
        dataframe['new_latitude'] = latitude
        dataframe['new_longitude'] = longitude
    except Exception as e:
        # Handle any potential errors during transformation
        # print(f"Error during UTM to Lat/Lon conversion: {e}")
        messages.error(request, f"Error during UTM to Lat/Lon conversion: {e}")

    return dataframe


#  ============================= Convert projected coordinates (UTM) from feet to meter =============================

#function to convert northing and easting coordinates into meter if they are in feet
def feet_to_meter(dataframe, easting_col, northing_col):
    # Conversion factor from feet to meters
    feet_to_meters = 0.3048

    # Check if the columns exist in the DataFrame
    if easting_col not in dataframe.columns:
        raise ValueError(f"Column '{easting_col}' not found in the DataFrame.")
    if northing_col not in dataframe.columns:
        raise ValueError(f"Column '{northing_col}' not found in the DataFrame.")

    # Convert the values from feet to meters for the specified columns
    dataframe[easting_col] *= feet_to_meters
    dataframe[northing_col] *= feet_to_meters

    return dataframe


#  ============================= Convert projected coordinates (UTM) from KM to meter =============================

#function to convert northing and easting coordinates into meter if they are in kilometers
def km_to_meter(dataframe, easting_col, northing_col):
    # Conversion factor from kilometers to meters
    km_to_meters = 1000.0

    # Check if the columns exist in the DataFrame
    if easting_col not in dataframe.columns:
        raise ValueError(f"Column '{easting_col}' not found in the DataFrame.")
    if northing_col not in dataframe.columns:
        raise ValueError(f"Column '{northing_col}' not found in the DataFrame.")

    # Convert the values from kilometers to meters for the specified columns
    dataframe[easting_col] *= km_to_meters
    dataframe[northing_col] *= km_to_meters

    return dataframe