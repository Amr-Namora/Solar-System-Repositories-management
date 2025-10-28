from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Store

admin.site.register(Store)


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'is_staff', 'is_active','store')
    list_filter = ('is_staff', 'is_active')
    ordering = ('username',)
    search_fields = ['username']  # This will search through related Person fields

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Permissions'), {
            'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions','store','allowed_repositories')
        }),
        (_('Important dates'), {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'password1', 'password2', 'is_staff', 'is_active','store', 'allowed_repositories'),
            },
        ),
    )

    # Custom method to get related Person data



admin.site.register(CustomUser, CustomUserAdmin)
