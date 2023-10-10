import warnings
from django.http import JsonResponse
import pandas as pd
import re
from django.contrib import messages


#  ============================= Read CSv2 files =============================

def read_csv_file(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
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
    

#  ============================= Drop selected columns =============================

def drop_selected_column(df, selected_column):

    """
    Drop selected columns from dataframe

    df (dataframe): Input dataframe with all columns
    selected_column (column_name): Column user select

    """

    if selected_column in df.columns:
        df.drop(columns=selected_column, inplace=True, axis=1)


#  ============================= Impute missing values =============================

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


#  ============================= Drop rows =============================

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


#  ============================= Convert data types =============================

def convert_column_data_type(request, dataframe, column_name, new_data_type):
    try:
        # Check if the column exists in the DataFrame
        if column_name not in dataframe.columns:
            raise ValueError("Column '{}' does not exist in the DataFrame.".format(column_name))

        # Check if the column has any null values
        if dataframe[column_name].isnull().any():
            raise ValueError("Column '{}' has null values. Please clean the column before converting the data type.".format(column_name))

        # Validate the new_data_type
        valid_data_types = ['int', 'float', 'str', 'bool', 'date', 'datetime']
        if new_data_type not in valid_data_types:
            raise ValueError("Invalid data type '{}'. Valid data types are: {}.".format(new_data_type, ', '.join(valid_data_types)))

        # Check if the column contains only numeric values (int or float)
        if new_data_type in ['int', 'float']:
            non_numeric_chars = dataframe[column_name].apply(lambda x: bool(re.search(r'[^0-9.-]', str(x))))
            if non_numeric_chars.any():
                raise ValueError("Column '{}' contains non-numeric or special characters. Cannot convert to {}.".format(column_name, new_data_type))

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
        # messages.success(request, f"Column '{column_name}' converted to {new_data_type} data type successfully!")
        return dataframe
    except ValueError as ve:
        raise ValueError(str(ve))
    except Exception as e:
        raise ValueError('An unexpected error occurred')

    


#  ============================= Decimal GCS processing =============================

# Function to clean latitude and longitude in the dataframe
def extract_valid_lat_lon(lat_lon_str):
    # Remove leading/trailing whitespace from the string
    cleaned_str = lat_lon_str.strip()
    
    # Check if the string matches the latitude/longitude format using regex
    match = re.match(r'-?\d+\.\d+', cleaned_str)
    
    # Return the matched value if found, otherwise return NaN
    return float(match.group()) if match else float('NaN')

def convert_lat_lon_columns(request, dataframe, latitude_col, longitude_col):
    print("surprise mf")
    try:
        print(dataframe)
        # Check if the provided column names exist in the DataFrame
        if latitude_col not in dataframe.columns or longitude_col not in dataframe.columns:
            raise ValueError("Latitude or Longitude column does not exist in the DataFrame.")

        # Check if the latitude or longitude columns have NaN values
        if dataframe[latitude_col].isnull().any() or dataframe[longitude_col].isnull().any():
            raise ValueError("Latitude or Longitude columns contain NaN values, cannot process.")

        print(dataframe[latitude_col])
        print(dataframe[longitude_col])
        try:
            if dataframe[latitude_col].dtype == float and dataframe[longitude_col].dtype == float:
                pass
            else:
                # Convert latitude and longitude columns to numeric type using the custom function
                dataframe[latitude_col] = dataframe[latitude_col].apply(extract_valid_lat_lon)
                dataframe[longitude_col] = dataframe[longitude_col].apply(extract_valid_lat_lon)
        except Exception as e:
            # Handle the exception gracefully, e.g., by printing an error message
            raise ValueError(f"An error occurred while cleaning the coordinates: {str(e)}")

        # Drop rows with NaN values in latitude or longitude columns
        dataframe.dropna(subset=[latitude_col, longitude_col], inplace=True)

        # Add a success message
        # messages.success(request, f"Latitude and Longitude columns converted to numeric type successfully!")

    except ValueError as ve:
        # Raise a specific ValueError with the error message
        raise ValueError(str(ve))

    except Exception as e:
        # Raise a ValueError with a generic error message
        raise ValueError('An unexpected error occurred during computation')

    return dataframe