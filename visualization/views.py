from datetime import datetime
import os
from django.core.files import File
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.db import models
from django.core.management import call_command
from io import StringIO
from .models import MyFileModel  # Import your model
from django.apps import apps
from django.db import connection
import inspect
from django.contrib.auth.decorators import login_required
from app.json_serializable import json_to_geodataframe, json_to_dataframe, dataframe_to_json


@login_required(login_url='/Login/')
def home(request):
    return render(request, 'pages/index.html')

@login_required(login_url='/Login/')
def save_fbprophet(request):
    pass

@login_required(login_url='/Login/')
def save_arima(request):
    pass

@login_required(login_url='/Login/')
def save_geoDataFrame(request):
    pass

# @login_required(login_url='/Login/')
# def save_uploaded_dataFrame(request):
#     pass



# # Create a function to dynamically create a model
# def create_dynamic_model(dataframe, model_name):
#     class Meta:
#         managed = False
#         db_table = model_name

#     fields = {
#         column: models.CharField(max_length=255)  # Adjust the field type based on your data
#         for column in dataframe.columns
#     }
#     fields["id"] = models.AutoField(primary_key=True)

#     attrs = {
#         "__module__": __name__,
#         "Meta": Meta,
#         **fields,
#     }

#     return type(model_name, (models.Model,), attrs)

# # Assuming you have a view function
# def save_dataframe_to_database(request):
# # Assuming you have a DataFrame in the session variable named 'session_dataframe'
#     session_dataframe = request.session.get('data_frame')
#     session_dataframe = json_to_dataframe(session_dataframe)

#     # Define a model name (you can customize this)
#     model_name = 'iris'

#     # Create the dynamic model
#     dynamic_model = create_dynamic_model(session_dataframe, model_name)

#     # Create the table in the SQLite database
#     with connection.schema_editor() as schema_editor:
#         schema_editor.create_model(dynamic_model)

#     # Iterate through the DataFrame rows and save them to the database
#     for _, row in session_dataframe.iterrows():
#         instance = dynamic_model()
#         for column, value in row.items():
#             setattr(instance, column, value)
#         instance.save()

#     return render(request, 'pages/index.html')  # Replace 'your_template.html' with the desired template    return render(request, 'home.html', {'message': 'Data not found in session'})

def save_dataframe_to_database(request, df, name):
    # session_dataframe = request.session.get('data_frame')
    # df = json_to_dataframe(session_dataframe)

    # Define the filename
    # Generate a timestamp to append to the filename
    # timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    file_name = name

    # Check if a file with the same name exists in the database
    existing_file = MyFileModel.objects.filter(file__contains=file_name).first()

    if existing_file:
        print("existing file: ", existing_file.file.name)
        # Delete the existing file from the database
        existing_file.delete()

    # Create a new instance of MyFileModel
    my_file_instance = MyFileModel(user=request.user)

    # Create a path for the CSV file within the app's media folder
    media_path = os.path.join(settings.MEDIA_ROOT, file_name)

    if os.path.exists(media_path):
        os.remove(media_path)

    # Save the DataFrame to the CSV file
    df.to_csv(media_path, index=False)
    with open(media_path, 'rb') as file:
        my_file_instance.file.save(file_name, File(file))
    
    my_file_instance.save()

    return HttpResponse("CSV file uploaded to the database successfully.")




       