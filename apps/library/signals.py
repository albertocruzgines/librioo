from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import Chapter, BookSubscription
from apps.notifications.models import Notification

@receiver(post_save, sender=Chapter)
def notify_new_chapter(sender, instance, created, **kwargs):
    if not created:
        return
    # If chapter is already published at creation, notify subscribers
    if instance.is_visible:
        subs = BookSubscription.objects.filter(book=instance.book).select_related('user')
        ct = ContentType.objects.get_for_model(Chapter)
        for s in subs:
            Notification.objects.create(
                user=s.user,
                verb=f'Nuevo capítulo publicado: {instance.title}',
                content_type=ct,
                object_id=instance.id
            )
