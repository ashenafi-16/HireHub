from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, CustomerProfile, ProviderProfile

class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    verbose_name_plural = 'Customer Profile'
    fk_name = 'user'

class ProviderProfileInline(admin.StackedInline):
    model = ProviderProfile
    can_delete = False
    verbose_name_plural = 'Provider Profile'
    fk_name = 'user'
    

class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    ordering = ('email',)
    search_fields = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('user_type',)}),
        (_('Permissions'), {
            'fields': ('is_verified','is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'user_type', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

    def get_inlines(self, request, obj=None):
        if not obj:
            return []
        if obj.user_type == 'customer':
            return [CustomerProfileInline]
        elif obj.user_type == 'provider':
            return [ProviderProfileInline]
        return []

admin.site.register(User, UserAdmin)
admin.site.register(CustomerProfile)
admin.site.register(ProviderProfile)
