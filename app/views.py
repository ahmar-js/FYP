import pandas as pd
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from .forms import UploadFileForm
import re
import io
import time
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from django.contrib import messages
import pyproj
# def upload_filee(request):
#     if request.method == 'POST':
#         form = UploadFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             # Read the uploaded file using Pandas
#             uploaded_file = request.FILES['file']
#             df = pd.read_csv(uploaded_file)

#             # Process the data as needed
#             # For example, you can display the first few rows of the CSV data
#             preview_data = df.head()

#             # Pass the preview_data to the template to display
#             return render(request, 'preview.html', {'preview_data': preview_data})

#     else:
#         form = UploadFileForm()

#     return render(request, 'upload.html', {'form': form})



def read_csv_file(file_path):
    try:
        df = pd.read_csv(file_path)
        df = pd.DataFrame(df)
        return df
    except pd.errors.EmptyDataError:
        raise Exception('The CSV file is empty.')
    except pd.errors.ParserError:
        raise Exception('Error parsing the CSV file. Please ensure it is a valid CSV file.')
    except FileNotFoundError:
        raise Exception('The CSV file does not exist.')
    except Exception as e:
        raise Exception('An error occurred while reading the CSV file: ' + str(e))

#Function to drop selected columns
def drop_selected_column(df, selected_column):

    """
    Drop selected columns from dataframe

    df (dataframe): Input dataframe with all columns
    selected_column (column_name): Column user select

    """

    if selected_column in df.columns:
        df.drop(columns=selected_column, inplace=True, axis=1)


# Function to handle missing values
def handle_missing_values(data, strategy='mean', columns=None):
    """
    Handle missing values in the dataset using specified strategy.

    Parameters:
        data (pd.DataFrame): Input DataFrame with missing values.
        strategy (str): Strategy to impute missing values. Options: 'mean', 'median', 'most_frequent', 'constant'.
        columns (list): List of columns to apply the imputation. If None, imputes all columns with missing values.

    Returns:
        pd.DataFrame: DataFrame with missing values imputed.
    """
    try:
        if columns is None:
            columns = data.columns[data.isnull().any()]

        for col in columns:
            if strategy == 'mean':
                data[col].fillna(data[col].mean(), inplace=True)
            elif strategy == 'median':
                data[col].fillna(data[col].median(), inplace=True)
            elif strategy == 'most_frequent':
                data[col].fillna(data[col].mode()[0], inplace=True)
            elif strategy == 'bfill':
                data[col].fillna(method='bfill', inplace=True)
            elif strategy == 'pad':
                data[col].fillna(method='pad', inplace=True)
            else:
                # If strategy is 'constant', you can provide a specific constant value.
                data[col].fillna(strategy, inplace=True)
    except Exception as e:
        raise Exception('Error: Fill null Values: ' + str(e))
    return data


# drop null values
def drop_rows(dataframe, how='any', subset=None):
    """
    Drop rows from a Pandas DataFrame based on specified conditions.

    Parameters:
        dataframe (pd.DataFrame): The DataFrame to drop rows from.
        how (str, optional): The technique to use when dropping rows. Default is 'any'.
            'any': Drop rows if any of the values in the subset columns are null.
            'all': Drop rows if all of the values in the subset columns are null.
        subset (list or None, optional): A list of column names to consider for dropping rows based on their values. 
            If None, all columns will be considered. Default is None.

    Returns:
        pd.DataFrame: The DataFrame with rows dropped based on the specified conditions.
    """
    try:
        if subset is not None:
            if how not in ['any', 'all']:
                raise ValueError("Invalid value for 'how'. It should be 'any' or 'all'.")

            # Drop rows based on 'how' and the specified subset of columns
            dataframe = dataframe.dropna(how=how, subset=subset, inplace=True)
        else:
            # Drop rows if any value in any column is null
            dataframe = dataframe.dropna(how=how, inplace=True)

    except ValueError as e:
        print("Error: ", e)

    return dataframe



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


#function to change the column data type

def convert_column_data_type(request, dataframe, column_name, new_data_type):
    # Check if the column exists in the DataFrame
    if column_name not in dataframe.columns:
        messages.error(request, "Error: Column '{}' does not exist in the DataFrame.".format(column_name))
        return dataframe

    # Check if the column has any null values
    if dataframe[column_name].isnull().any():
        messages.error(request, "Error: Column '{}' has null values. Please clean the column before converting the data type.".format(column_name))
        return dataframe

    # Validate the new_data_type
    valid_data_types = ['int', 'float', 'str', 'bool', 'date', 'datetime']
    if new_data_type not in valid_data_types:
        messages.error(request, "Error: Invalid data type '{}'. Valid data types are: {}.".format(new_data_type, ', '.join(valid_data_types)))
        return dataframe

    # Check if the column contains only numeric values (int or float)
    if new_data_type in ['int', 'float']:
        non_numeric_chars = dataframe[column_name].apply(lambda x: bool(re.search(r'[^0-9.-]', str(x))))
        if non_numeric_chars.any():
            messages.error(request, "Error: Column '{}' contains non-numeric or special characters. Cannot convert to {}.".format(column_name, new_data_type))
            return dataframe

    try:
        # Convert the column data type based on the new_data_type
        if new_data_type == 'int':
            dataframe[column_name] = dataframe[column_name].astype(int)
        elif new_data_type == 'float':
            dataframe[column_name] = dataframe[column_name].astype(float)
        elif new_data_type == 'str':
            dataframe[column_name] = dataframe[column_name].astype(str)
        elif new_data_type == 'bool':
            dataframe[column_name] = dataframe[column_name].astype(bool)
        elif new_data_type == 'date':
            dataframe[column_name] = pd.to_datetime(dataframe[column_name]).dt.date
        elif new_data_type == 'datetime':
            dataframe[column_name] = pd.to_datetime(dataframe[column_name])

        # Add a success message
        messages.success(request, f"Column '{column_name}' converted to {new_data_type} data type successfully!")
    except Exception as e:
        messages.error(request, f"Error: Failed to convert column '{column_name}'. Error: {e}")

    return dataframe

#function to clean latitude and longitude in the dataframe

def extract_valid_lat_lon(lat_lon_str):
    # Remove leading/trailing whitespace from the string
    cleaned_str = lat_lon_str.strip()
    
    # Check if the string matches the latitude/longitude format using the regex
    match = re.match(r'-?\d+\.\d+', cleaned_str)
    
    # Return the matched value if found, otherwise return NaN
    return float(match.group()) if match else float('NaN')

def convert_lat_lon_columns(request, dataframe, latitude_col, longitude_col):
    # Check if the provided column names exist in the DataFrame
    if latitude_col not in dataframe.columns or longitude_col not in dataframe.columns:
        messages.error(request, "Error: Latitude or Longitude column does not exist in the DataFrame.")
        return dataframe
    if dataframe[latitude_col].isnull().any() or dataframe[longitude_col].isnull().any():
        messages.error(request, "Error: Connot process NaN values.")
        return dataframe

    # Convert latitude and longitude columns to numeric type using the custom function
    try:
        if not dataframe[latitude_col].dtype is float and not dataframe[longitude_col].dtype == float:
            dataframe[latitude_col] = dataframe[latitude_col].apply(extract_valid_lat_lon)
            dataframe[longitude_col] = dataframe[longitude_col].apply(extract_valid_lat_lon)
            # Add a success message
            messages.success(request, f"Latitude and Longitude columns converted to numeric type successfully!")
            # Drop rows with NaN values in latitude or longitude columns
            dataframe.dropna(subset=[latitude_col, longitude_col], inplace=True)
            messages.success(request, f"Computation Success!")
        else:
            messages.success(request, f"Computation Success!")

    except Exception as e:
        messages.error(request, f"Error: Failed to convert latitude/longitude columns. Error: {e}")


    return dataframe

#functions to convert handle DMS coordinates and convert into decimal degrees


'''
this function still assumes that the DMS strings are provided in a consistent format 
with degree (°), minute (' or m), and second (" or s) symbols separated by whitespace. 
The function performs checks to ensure valid values for degrees, minutes, and seconds. 
Additionally, it handles the hemisphere (N, S, E, W) correctly for positive or negative 
values in the Decimal Degree format.
'''

def dms_to_decimal(dms_str, request=None):
    # Regular expression pattern to extract DMS components
    dms_pattern = r'^\s*(?P<degrees>\d+)[°d]\s*((?P<minutes>\d+)[\'m])?\s*((?P<seconds>\d+(\.\d+)?)?["s]?)?\s*([NSWE]?)\s*$'
    match = re.match(dms_pattern, dms_str)

    if not match:
        if request:
            messages.error(request, f"Error: Invalid DMS format for '{dms_str}'.")
        raise ValueError(f"Invalid DMS format for '{dms_str}'")

    degrees = float(match.group('degrees'))
    minutes = float(match.group('minutes') or 0)
    seconds = float(match.group('seconds') or 0)

    # Check for invalid values
    if degrees < 0 or degrees >= 360:
        if request:
            messages.error(request, "Degrees should be between 0 and 359.")
        raise ValueError("Degrees should be between 0 and 359.")
    if minutes < 0 or minutes >= 60:
        if request:
            messages.error(request, "Minutes should be between 0 and 59.")
        raise ValueError("Minutes should be between 0 and 59.")
    if seconds < 0 or seconds >= 60:
        if request:
            messages.error(request, "Seconds should be between 0 and 59.9999.")
        raise ValueError("Seconds should be between 0 and 59.9999.")

    # Calculate the Decimal Degree value
    decimal_deg = degrees + minutes / 60 + seconds / 3600

    # Check the hemisphere (N, S, E, W)
    hemisphere = match.group(6) or ''
    if hemisphere.upper() in ['S', 'W']:
        decimal_deg = -decimal_deg

    return decimal_deg

def convert_dms_to_decimal(request, dataframe, latitude_col, longitude_col):
    # Check if the provided column names exist in the DataFrame
    if latitude_col not in dataframe.columns or longitude_col not in dataframe.columns:
        messages.error(request, "Error: Latitude or Longitude column does not exist in the DataFrame.")
        return dataframe

    try:
        # Convert latitude and longitude columns to Decimal Degree format
        dataframe[latitude_col] = dataframe[latitude_col].apply(dms_to_decimal, request=request)
        dataframe[longitude_col] = dataframe[longitude_col].apply(dms_to_decimal, request=request)

        # Drop rows with missing or invalid values in latitude or longitude columns
        dataframe.dropna(subset=[latitude_col, longitude_col], inplace=True)

        # Add a success message
        messages.success(request, "Latitude and Longitude columns converted to Decimal Degree format successfully!")

    except Exception as e:
        messages.error(request, f"Error: Failed to convert latitude/longitude columns. Error: {e}")

    return dataframe

def geocode_address(request, address):
    geolocator = Nominatim(user_agent="ahmaraamir33@gmail.com", timeout=10000)
    try:
        # Introduce a delay of 1 second before making the geocoding request
        time.sleep(1)
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception as e:
        messages.error(request, f"Geocoding error for address: {address}, Error: {e}")
        return None, None

def concatenate_and_geocode(request, dataframe, columns_to_concatenate):
    # Check if the user selects only one column (direct geocoding)
    if len(columns_to_concatenate) == 1:
        address_col = columns_to_concatenate[0]
        latitude_list, longitude_list = [], []
        for index, row in dataframe.iterrows():
            lat, lon = geocode_address(request, row[address_col])
            latitude_list.append(lat)
            longitude_list.append(lon)
        # Assign the latitude and longitude lists to the DataFrame
        dataframe['plat'] = latitude_list
        dataframe['plong'] = longitude_list
    else:
        # Check if the provided column names exist in the DataFrame
        for col in columns_to_concatenate:
            if col not in dataframe.columns:
                messages.error(request, f"Error: Column '{col}' does not exist in the DataFrame.")
                return dataframe

        try:
            # Concatenate the values of the specified columns into a new column
            new_column_name = 'concatenated_address'
            dataframe[new_column_name] = dataframe[columns_to_concatenate].astype(str).apply(' '.join, axis=1)

            # Call geocode_address_with_delay for each concatenated address
            latitude_list, longitude_list = [], []
            for index, row in dataframe.iterrows():
                lat, lon = geocode_address(request, row[new_column_name])
                latitude_list.append(lat)
                longitude_list.append(lon)

            # Drop the concatenated column after geocoding
            # dataframe.drop(columns=[new_column_name], inplace=True)

            # Assign the latitude and longitude lists to the DataFrame
            dataframe['plat'] = latitude_list
            dataframe['plong'] = longitude_list

        except Exception as e:
            messages.error(request, f"Error: Failed to concatenate columns or perform geocoding. Error: {e}")

    return dataframe

#-------------------- Reverse Geocoding ---------------------------

# Reverse Geocoding
def is_valid_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def rev_geocode(request, latitude, longitude):
    if not is_valid_float(latitude) or not is_valid_float(longitude):
        messages.error(request, "Error: Latitude and Longitude should be valid floating-point numbers.")
        return None

    geolocator = Nominatim(user_agent="ahmaraamir33@gmail.com")
    reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)
    try:
        location = reverse((latitude, longitude), exactly_one=True, language='en', timeout=10)
        if location:
            address = location.address
            return address
        else:
            messages.warning(request, f"Warning: Address not found for latitude={latitude}, longitude={longitude}")
            return None
    except Exception as e:
        messages.error(request, f"Error: Failed to reverse geocode for latitude={latitude}, longitude={longitude}. Error: {e}")
        return None

def convert_lat_lng_to_addresses(request, dataframe, lat, long):
    if lat not in dataframe.columns or long not in dataframe.columns:
        messages.error(request, f"Error: Latitude or Longitude column does not exist in the DataFrame.")
        return dataframe

    # Check if the provided columns contain valid float values
    if not all(dataframe[lat].apply(is_valid_float)) or not all(dataframe[long].apply(is_valid_float)):
        messages.error(request, "Error: Latitude and Longitude columns should contain valid floating-point numbers.")
        return dataframe

    addresses = []
    for index, row in dataframe.iterrows():
        latitude = row[lat]
        longitude = row[long]
        address = rev_geocode(request, latitude, longitude)
        if address is not None:
            addresses.append(address)

    if len(addresses) == 0:
        messages.warning(request, "Warning: No valid addresses found for the provided latitude and longitude columns.")
        return dataframe

    dataframe['new_address'] = addresses
    return dataframe



'''
DataFrames are not natively JSON serializable.

converting the DataFrame to a JSON serializable format before storing it in the session 
and convert it back to a DataFrame when retrieving it from the session.

'''

def dataframe_to_json(df):
    return df.to_json(orient='split')

def json_to_dataframe(json_data):
    return pd.read_json(json_data, orient='split')

def preview_dataframe(df, limit=10):
    return df.head(limit)



def update_stats(df):
    preview_data = preview_dataframe(df)
    num_rows = df.shape[0]
    num_cols = df.shape[1]
    total_nulls = df.isnull().sum().sum()
    total_notnull = df.notnull().sum().sum()
    unique_dtypes = len(df.dtypes.unique())
    df_dtype_info = df.dtypes

        
    return preview_data, num_rows, num_cols, total_nulls, total_notnull, unique_dtypes, df_dtype_info

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

    # Check if the "reset" parameter is in POST data
    if request.method == 'POST' and 'reset' in request.POST:
        print("here")
        # request.session.clear()  # Clear the entire session
        request.session.pop('data_frame', None)
        # del request.session['data_frame']
        # return redirect('upload')

    # Show the stats at the initial level
    preview_data, num_rows, num_cols, total_nulls, total_notnull, unique_dtypes, df_dtype_info = update_stats(df)


    if request.method == 'POST':
        try:

            # Process different POST requests and modify DataFrame accordingly
            if 'dropcolumnmenu' in request.POST:
                # Drop selected columns
                selected_column = request.POST['dropcolumnmenu']
                drop_selected_column(df, selected_column)

            elif 'fillnullvalues' in request.POST and 'strategy' in request.POST:
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

            # Get the user-selected number of rows to display
            if request.POST.get('datalimit') != 'all':
                data_limit = int(request.POST.get('datalimit', 10))
            else:
                #show complete data
                data_limit = df.shape[0]
                
            # Limit the number of rows to display
            preview_data = preview_dataframe(df, limit=data_limit)

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






# def total_columns(self):
#     return self.


