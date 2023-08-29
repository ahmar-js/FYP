from django.contrib import messages
import time
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim


#  ============================= Forward Geocoding =============================

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


#  ============================= Reverse Geocoding =============================

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