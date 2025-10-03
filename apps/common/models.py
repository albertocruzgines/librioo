from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = settings.AUTH_USER_MODEL

class Report(models.Model):
    REPORT_TYPES = (('abuse','Contenido inapropiado'),('plagiarism','Plagio'))
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type','object_id')
    kind = models.CharField(max_length=20, choices=REPORT_TYPES)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
