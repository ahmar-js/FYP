import pandas as pd
from django.shortcuts import render
from django.http import HttpResponseRedirect
from .forms import UploadFileForm

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

'''
DataFrames are not natively JSON serializable.

converting the DataFrame to a JSON serializable format before storing it in the session 
and convert it back to a DataFrame when retrieving it from the session.

'''

def dataframe_to_json(df):
    return df.to_json(orient='split')

def json_to_dataframe(json_data):
    return pd.read_json(json_data, orient='split')

def preview_dataframe(df):
    return df.head(11)



def update_stats(df):
    preview_data = preview_dataframe(df)
    num_rows = df.shape[0]
    num_cols = df.shape[1]
    total_nulls = df.isnull().sum().sum()
    unique_dtypes = len(df.dtypes.unique())
    df_dtype_info = df.dtypes

    return preview_data, num_rows, num_cols, total_nulls, unique_dtypes, df_dtype_info

def upload_file(request):
    file_path = 'C:/Users/User/Desktop/ahm/MALARIA.csv'
    preview_data = None

    # Check for the 'reset' parameter in POST data
    if request.method == 'POST' and 'reset' in request.POST:
        # request.session.pop('data_frame', None)  # Remove the 'data_frame' from the session 
        request.session.clear()  # Clear the entire session

    # Initialize DataFrame from session or read the CSV file
    json_data = request.session.get('data_frame')
    if json_data is None:
        try:
            df = read_csv_file(file_path)
            request.session['data_frame'] = dataframe_to_json(df)
        except Exception as e:
            return render(request, 'error.html', {'error_message': str(e)})
    else:
        df = json_to_dataframe(json_data)


    # Show the stats at initial level
    preview_data, num_rows, num_cols, total_nulls, unique_dtypes, df_dtype_info = update_stats(df)


    if request.method == 'POST':
        try:
            # Check if the 'dropcolumnmenu' field is in the POST data
            if 'dropcolumnmenu' in request.POST:
                selected_column = request.POST['dropcolumnmenu']
                drop_selected_column(df, selected_column)
                # Update the DataFrame in the session
                request.session['data_frame'] = dataframe_to_json(df)

                # Update the statistics with the modified DataFrame
                preview_data, num_rows, num_cols, total_nulls, unique_dtypes, df_dtype_info = update_stats(df)
            
            
            if 'fillnullvalues' in request.POST and 'strategy' in request.POST:
                selected_column = request.POST['fillnullvalues']
                selected_strategy = request.POST['strategy']
                # To impute constant
                if selected_strategy == 'input_constant':
                    selected_strategy = request.POST['strategy_constant']

                if selected_column == 'complete_data':
                    handle_missing_values(df, strategy=selected_strategy)
                else:
                    handle_missing_values(df, strategy=selected_strategy, columns=[selected_column])

                # Update the DataFrame in the session
                request.session['data_frame'] = dataframe_to_json(df)

                # Update the statistics with the modified DataFrame
                preview_data, num_rows, num_cols, total_nulls, unique_dtypes, df_dtype_info = update_stats(df)
            
            elif 'fillnullvalues' in request.POST and 'strategy_constant' in request.POST:
                selected_column = request.POST['fillnullvalues']
                selected_strategy = request.POST['strategy_constant']
                if selected_column == 'complete_data':
                    handle_missing_values(df, strategy=selected_strategy)
                else:
                    handle_missing_values(df, strategy=selected_strategy, columns=[selected_column])
                # Update the DataFrame in the session
                request.session['data_frame'] = dataframe_to_json(df)
                # Update the statistics with the modified DataFrame
                preview_data, num_rows, num_cols, total_nulls, unique_dtypes, df_dtype_info = update_stats(df)

            if 'select-multi-drop-row' in request.POST or 'row_drop_strategy' in request.POST:
                
                selected_column = request.POST.get('select-multi-drop-row', None)
                selected_strategy = request.POST.get('row_drop_strategy', None)

                drop_rows(df, how=selected_strategy, subset=selected_column)

                # Update the DataFrame in the session
                request.session['data_frame'] = dataframe_to_json(df)
                # Update the statistics with the modified DataFrame
                preview_data, num_rows, num_cols, total_nulls, unique_dtypes, df_dtype_info = update_stats(df)

            



        except Exception as e:
            return render(request, 'error.html', {'error_message': 'An error occurred: ' + str(e)})
    
    context = {
        'df_info': df_dtype_info,
        'preview_data': preview_data,
        'num_columns': num_cols,
        'num_rows': num_rows,
        'tot_nulls': total_nulls,
        'unique_dtypes': unique_dtypes,
    }

    return render(request, 'preview.html', context)






# def total_columns(self):
#     return self.


