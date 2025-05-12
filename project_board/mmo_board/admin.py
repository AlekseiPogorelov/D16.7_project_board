from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Article, UserResponse, Subscription, Category, User


from django.contrib.auth.models import User as AuthUser
if admin.site.is_registered(AuthUser):
    admin.site.unregister(AuthUser)


if admin.site.is_registered(User):
    admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


admin.site.register(Article)
admin.site.register(UserResponse)
admin.site.register(Subscription)
admin.site.register(Category)


