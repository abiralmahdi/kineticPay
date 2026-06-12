from django.contrib import admin
from django.apps import apps

# Get the current app's configuration based on this file's package name
current_app = apps.get_containing_app_config(__name__)

# Loop through every model registered under this specific app
for model_name, model in current_app.models.items():
    
    # Define a custom ModelAdmin class dynamically to enhance the UI
    class DynamicModelAdmin(admin.ModelAdmin):
        # Display all fields in the admin list view automatically
        list_display = [field.name for field in model._meta.fields]
        
        # Optional: Add a search bar for the first text/char field found in the model
        search_fields = [
            field.name for field in model._meta.fields 
            if field.get_internal_type() in ['CharField', 'TextField']
        ][:1] # Limits to the first match to prevent errors on non-indexable fields

    try:
        # Register the model with its custom dynamic configuration
        admin.site.register(model, DynamicModelAdmin)
    except admin.sites.AlreadyRegistered:
        # Fail silently if a model was already registered manually elsewhere
        pass