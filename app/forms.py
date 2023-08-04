from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(label='Select a csv file', required=True, widget=forms.FileInput(attrs={'class': 'form-control upload-file', 'accept': '.csv', 'id': 'Upload_file'}))

