import pandas as pd
import json

'''
DataFrames are not natively JSON serializable.

converting the DataFrame to a JSON serializable format before storing it in the session 
and convert it back to a DataFrame when retrieving it from the session.

'''

def dataframe_to_json(df):
    return df.to_json(orient='records')




def json_to_dataframe(json_data):
     data = json.loads(json_data)
     return pd.DataFrame(data)
