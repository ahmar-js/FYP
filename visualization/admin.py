from django.contrib import admin

from .models import Uploaded_DataFrame, geoDataFrame, fbProphet_forecasts, ARIMA_forecasts

class Uploaded_DataFrameAdmin(admin.ModelAdmin):
    list_display = ['user', 'file', 'uploaded_at', 'updated_at']

class geoDataFrameAdmin(admin.ModelAdmin):
    list_display = ['U_df', 'file', 'uploaded_at', 'updated_at']

class fbProphet_forecastsAdmin(admin.ModelAdmin):
    list_display = ['U_df', 'filtered_by', 'period', 'frequency', 'file', 'uploaded_at', 'updated_at']
class ARIMA_forecastsAdmin(admin.ModelAdmin):
    list_display = ['U_df', 'filtered_by', 'period', 'file', 'uploaded_at', 'updated_at']


admin.site.register(Uploaded_DataFrame, Uploaded_DataFrameAdmin)
admin.site.register(geoDataFrame, geoDataFrameAdmin)
admin.site.register(fbProphet_forecasts, fbProphet_forecastsAdmin)
admin.site.register(ARIMA_forecasts, ARIMA_forecastsAdmin)

