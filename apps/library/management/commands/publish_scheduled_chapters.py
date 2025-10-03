from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.library.models import Chapter

class Command(BaseCommand):
    help = 'Publica capítulos programados cuya fecha/hora ya pasó.'

    def handle(self, *args, **options):
        now = timezone.now()
        qs = Chapter.objects.filter(status='scheduled', publish_at__lte=now)
        count = 0
        for ch in qs:
            ch.status = 'published'
            ch.save(update_fields=['status'])
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Publicados {count} capítulos.'))
