from django import forms
from django.utils import timezone
from django.conf import settings
from .models import Chapter

class ChapterForm(forms.ModelForm):
    # Sobrescribimos para usar datetime-local (calendario + hora nativo)
    publish_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "class": "form-control",
                "placeholder": "YYYY-MM-DDTHH:MM",
            }
        ),
        input_formats=["%Y-%m-%dT%H:%M"],  # formato que envía datetime-local
    )

    class Meta:
        model = Chapter
        fields = ["number", "title", "content", "status", "publish_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formatear initial para que el input muestre valor correcto
        if self.instance and self.instance.publish_at:
            dt = timezone.localtime(self.instance.publish_at)
            self.initial["publish_at"] = dt.strftime("%Y-%m-%dT%H:%M")

    def clean_publish_at(self):
        value = self.cleaned_data.get("publish_at")
        if not value:
            return None
        # Hacer aware si viene ingenuo (datetime-local no trae tz)
        if settings.USE_TZ and timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return value
