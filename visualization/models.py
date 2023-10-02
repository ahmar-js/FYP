from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Uploaded_DataFrame(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads_df/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} - {self.file.name}'

class geoDataFrame(models.Model):
    U_df = models.ForeignKey(Uploaded_DataFrame, on_delete=models.CASCADE, blank=True, null=True)
    file = models.FileField(upload_to='uploads_gdf/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.file.name}'
    
class fbProphet_forecasts(models.Model):
    U_df = models.ForeignKey(Uploaded_DataFrame, on_delete=models.CASCADE, blank=True, null=True)
    filtered_by = models.CharField(max_length=255)
    period = models.PositiveIntegerField(null=False, blank=False)
    frequency = models.CharField(max_length=255, null=False, blank=False)
    file = models.FileField(upload_to='uploads_fb_forecasts/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.file.name} - {self.filtered_by}'

class ARIMA_forecasts(models.Model):
    U_df = models.ForeignKey(Uploaded_DataFrame, on_delete=models.CASCADE, blank=True, null=True)
    filtered_by = models.CharField(max_length=255)
    period = models.PositiveIntegerField(null=False, blank=False)
    file = models.FileField(upload_to='uploads_ar_ma_forecasts/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.file.name} - {self.filtered_by}'
    
class ConfigDashboard(models.Model):
    U_df = models.ForeignKey(Uploaded_DataFrame, on_delete=models.CASCADE, blank=True, null=True)
    U_gdf = models.ForeignKey(geoDataFrame, on_delete=models.CASCADE, blank=True, null=True)
    latitude = models.CharField(max_length=255, null=False, blank=False)
    longitude = models.CharField(max_length=255, null=False, blank=False)
    filtered = models.CharField(max_length=255, null=False, blank=False)
    color = models.CharField(max_length=255, null=False, blank=False)
    location = models.CharField(max_length=255, null=False, blank=False)
    hover_data = models.CharField(max_length=255, null=False, blank=False)
    date = models.CharField(max_length=255, null=False, blank=False)
    size = models.CharField(max_length=255, null=False, blank=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'config_dashboard'


