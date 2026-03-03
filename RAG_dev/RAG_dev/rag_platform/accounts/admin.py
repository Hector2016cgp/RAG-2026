from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('bio', 'avatar', 'preferred_engine')}),
    )
    list_display = ['username', 'email', 'first_name', 'last_name', 'preferred_engine', 'is_staff']
    list_filter = ['preferred_engine', 'is_staff', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
