from django.db import models
from django.conf import settings
from apps.library.models import Book

User = settings.AUTH_USER_MODEL

class Payment(models.Model):
    PROVIDERS = (('stripe','Stripe'),)
    STATUS = (('created','Creado'),('paid','Pagado'),('failed','Fallido'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='payments')
    provider = models.CharField(max_length=20, choices=PROVIDERS, default='stripe')
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default='eur')
    status = models.CharField(max_length=20, choices=STATUS, default='created')
    external_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
