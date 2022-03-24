from django.contrib import admin

from .models import UserAccountModel, WaitingListUserAccountModel


# Register your models here.
@admin.register(UserAccountModel)
class UserAccountModelAdmin(admin.ModelAdmin):
    list_display = ('token', 'user')


@admin.register(WaitingListUserAccountModel)
class UserAccountModelAdmin(admin.ModelAdmin):
    list_display = ('user',)
