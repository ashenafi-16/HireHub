from django.contrib import admin
from authentication.models import CustomerProfile, ProviderProfile


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'location', 'is_profile_complete']
    search_fields = ['user__email', 'phone']
    list_filter = ['is_profile_complete']
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'phone', 'location', 'is_profile_complete')
        }),
    )


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'skills', 'service_area', 'hourly_rate', 'location', 'is_profile_complete']
    search_fields = ['user__email', 'service_area']
    list_filter = ['is_profile_complete']
    fieldsets = (
        ('Provider Information', {
            'fields': ('user', 'skills', 'service_area', 'hourly_rate', 'location', 'is_profile_complete')
        }),
    )
