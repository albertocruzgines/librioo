from django.contrib import admin
from .models import Post, Challenge, Club, ClubMembership, ClubPost
admin.site.register(Post)
admin.site.register(Challenge)
admin.site.register(Club)
admin.site.register(ClubMembership)
admin.site.register(ClubPost)
