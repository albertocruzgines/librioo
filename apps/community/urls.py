from django.urls import path
from . import views

app_name = 'community'
urlpatterns = [
    path('feed/', views.FeedView.as_view(), name='feed'),
    path('post/new/', views.PostCreateView.as_view(), name='post_new'),
    path('clubs/', views.ClubsView.as_view(), name='clubs'),
    path('clubs/<int:pk>/toggle/', views.toggle_membership, name='club_toggle'),
]
