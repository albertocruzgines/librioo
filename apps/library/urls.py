from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.LibraryHomeView.as_view(), name='home'),
    path('books/', views.BookListView.as_view(), name='book_list'),
    path('books/new/', views.BookCreateView.as_view(), name='book_create'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),
    path('books/<int:pk>/subscribe/', views.subscribe_book, name='subscribe_book'),
    path('books/<int:pk>/chapter/new/', views.ChapterCreateView.as_view(), name='chapter_create'),
    path('books/<int:pk>/edit/', views.BookUpdateView.as_view(), name='book_edit'),
    path('chapters/<int:pk>/', views.ChapterReadView.as_view(), name='chapter_read'),
    path('chapters/<int:pk>/comment/', views.create_comment, name='chapter_comment_create'),
    path('comments/<int:pk>/reply/', views.reply_comment, name='comment_reply'),
    path('react/<str:model>/<int:object_id>/<str:kind>/', views.react_toggle, name='react_toggle'),
    path('books/<int:pk>/review/', views.create_book_review, name='book_review_create'),
    path('books/<int:pk>/quote/', views.create_quote, name='quote_create'),
    path('polls/<int:poll_id>/vote/<int:option_id>/', views.vote_poll, name='vote_poll'),
    path('writer/dashboard/', views.WriterDashboardView.as_view(), name='writer_dashboard'),
    path('discover/', views.DiscoverView.as_view(), name='discover'),
    path('chapters/<int:pk>/edit/', views.ChapterUpdateView.as_view(), name='chapter_edit'),
    path('shelf/', views.ShelfView.as_view(), name='shelf'),
    path('shelf/set/<int:book_id>/<str:status>/', views.shelf_set_status, name='shelf_set_status'),
    path('shelf/set/<int:book_id>/<str:status>/', views.shelf_set_status, name='shelf_set_status'),
    path('shelf/remove/<int:book_id>/', views.shelf_remove, name='shelf_remove'),
    path('comments/<int:pk>/toggle_quote/', views.toggle_comment_quote, name='comment_toggle_quote'),
    path('chapters/<int:pk>/autosave/', views.chapter_autosave, name='chapter_autosave'),
    path('chapters/<int:pk>/revisions/', views.chapter_revisions, name='chapter_revisions'),
    path('chapters/<int:pk>/revisions/<int:rev_id>/restore/', views.chapter_revision_restore, name='chapter_revision_restore'),
    path('chapters/<int:pk>/save_version/', views.chapter_save_version, name='chapter_save_version'),
    path('uploads/images/', views.richtext_image_upload, name='richtext_image_upload'),
]
