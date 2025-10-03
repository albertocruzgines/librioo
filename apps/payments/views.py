import os
import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from apps.library.models import Book
from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
@require_POST
def checkout_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id, is_paid=True)
    amount = book.price_cents or 0
    if amount <= 0:
        return HttpResponseBadRequest('Precio inválido')

    # Create a Payment record
    pay = Payment.objects.create(user=request.user, book=book, amount_cents=amount, currency='eur')

    domain = request.build_absolute_uri('/').rstrip('/')
    try:
        session = stripe.checkout.Session.create(
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {'name': f'Libro: {{book.title}}'},
                    'unit_amount': amount,
                },
                'quantity': 1,
            }],
            success_url=f'{{domain}}/payments/success/{{pay.id}}/',
            cancel_url=f'{{domain}}/payments/cancel/{{pay.id}}/',
        )
    except Exception as e:
        pay.status = 'failed'
        pay.save(update_fields=['status'])
        return HttpResponseBadRequest('Error iniciando el pago')

    pay.external_id = session.id
    pay.save(update_fields=['external_id'])
    return redirect(session.url, permanent=False)

@login_required
def payment_success(request, payment_id):
    pay = get_object_or_404(Payment, pk=payment_id, user=request.user)
    pay.status = 'paid'
    pay.save(update_fields=['status'])
    return redirect('library:book_detail', pk=pay.book_id)

@login_required
def payment_cancel(request, payment_id):
    pay = get_object_or_404(Payment, pk=payment_id, user=request.user)
    pay.status = 'failed'
    pay.save(update_fields=['status'])
    return redirect('library:book_detail', pk=pay.book_id)
