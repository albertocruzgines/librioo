from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_writer = models.BooleanField(default=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    favorite_genres = models.JSONField(default=list, blank=True)  # simple list of strings

class UserFollow(models.Model):
    follower = models.ForeignKey('User', on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey('User', on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower','following')
