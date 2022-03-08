from django.contrib import admin

from .models import UserAccountModel


# Register your models here.
@admin.register(UserAccountModel)
class UserAccountModelAdmin(admin.ModelAdmin):
    list_display = ('token', 'user')
