from django.urls import path
from .views import checkout_book, payment_success, payment_cancel

app_name = 'payments'
urlpatterns = [
    path('checkout/book/<int:book_id>/', checkout_book, name='checkout_book'),
    path('success/<int:payment_id>/', payment_success, name='success'),
    path('cancel/<int:payment_id>/', payment_cancel, name='cancel'),
]
