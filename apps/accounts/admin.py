from django.contrib import admin
from .models import User, UserFollow

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username','email','is_writer')
    search_fields = ('username','email')

@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ('follower','following','created_at')
