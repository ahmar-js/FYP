import re
from django.contrib import messages


#  ============================= Convert DMS GCS to DGCS =============================

'''
this function still assumes that the DMS strings are provided in a consistent format 
with degree (°), minute (' or m), and second (" or s) symbols separated by whitespace. 
The function performs checks to ensure valid values for degrees, minutes, and seconds. 
Additionally, it handles the hemisphere (N, S, E, W) correctly for positive or negative 
values in the Decimal Degree format.
'''
#functions to convert handle DMS coordinates and convert into decimal degrees
def dms_to_decimal(dms_str, request=None):
    # Regular expression pattern to extract DMS components
    dms_pattern = r'^\s*(?P<degrees>\d+)[°d]\s*((?P<minutes>\d+)[\'m])?\s*((?P<seconds>\d+(\.\d+)?)?["s]?)?\s*([NSWE]?)\s*$'
    match = re.match(dms_pattern, dms_str)

    if not match:
        # if request:
        #     messages.error(request, f"Error: Invalid DMS format for '{dms_str}'.")
        raise ValueError(f"Invalid DMS format for '{dms_str}'")

    degrees = float(match.group('degrees'))
    minutes = float(match.group('minutes') or 0)
    seconds = float(match.group('seconds') or 0)

    # Check for invalid values
    if degrees < 0 or degrees >= 360:
        # if request:
        #     messages.error(request, "Degrees should be between 0 and 359.")
        raise ValueError("Degrees should be between 0 and 359.")
    if minutes < 0 or minutes >= 60:
        # if request:
        #     messages.error(request, "Minutes should be between 0 and 59.")
        raise ValueError("Minutes should be between 0 and 59.")
    if seconds < 0 or seconds >= 60:
        # if request:
        #     messages.error(request, "Seconds should be between 0 and 59.9999.")
        raise ValueError("Seconds should be between 0 and 59.9999.")

    # Calculate the Decimal Degree value
    decimal_deg = degrees + minutes / 60 + seconds / 3600

    # Check the hemisphere (N, S, E, W)
    hemisphere = match.group(6) or ''
    if hemisphere.upper() in ['S', 'W']:
        decimal_deg = -decimal_deg

    return decimal_deg

def convert_dms_to_decimal(request, dataframe, latitude_col, longitude_col):
    try:
        # Check if the provided column names exist in the DataFrame
        if latitude_col not in dataframe.columns or longitude_col not in dataframe.columns:
            raise ValueError("Error: Latitude or Longitude column does not exist in the DataFrame.")
        try:
            # Convert latitude and longitude columns to Decimal Degree format
            dataframe[latitude_col] = dataframe[latitude_col].apply(dms_to_decimal, request=request)
            dataframe[longitude_col] = dataframe[longitude_col].apply(dms_to_decimal, request=request)

            # Drop rows with missing or invalid values in latitude or longitude columns
            dataframe.dropna(subset=[latitude_col, longitude_col], inplace=True)
        except Exception as e:
            raise ValueError(f"Failed to convert latitude/longitude columns. Ensure that DMS strings are provided in a consistent format with degree (°), minute (' or m), and second (' or s) symbols [Error: {str(e)}]")
    except ValueError as ve:
        # Raise a specific ValueError with the error message
        raise ValueError(str(ve))
    except Exception as e:
            raise ValueError("An Unexpected error occurred while in dms conversion.")
        

    return dataframe