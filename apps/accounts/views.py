# accounts/views.py
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView
from django.urls import reverse_lazy
from django import forms

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from apps.library.models import Book  # <-- importa tu modelo Book

User = get_user_model()

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['avatar', 'bio', 'favorite_genres', 'is_writer']
        widgets = {'bio': forms.Textarea(attrs={'rows': 4})}

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Libros del usuario
        qs = (Book.objects
              .filter(author=self.request.user)
              .select_related('category')
              .prefetch_related('subscribers'))  # para contar subs sin N+1

        # Paginación
        page = self.request.GET.get('page', 1)
        paginator = Paginator(qs, 6)  # 6 por página (ajusta a tu gusto)
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        # Estadísticas (sobre TODO el queryset del usuario)
        # Usamos getattr con default para que no falle si el campo no existe
        subs_total = 0
        reads_total = 0
        views_total = 0
        for b in qs:
            # gracias a prefetch, .all() no golpea la BD por cada libro
            subs_total += b.subscribers.all().count()
            reads_total += (getattr(b, 'reads_count', 0) or 0)
            views_total += (getattr(b, 'views', 0) or 0)

        ctx.update({
            'my_books': page_obj.object_list,  # lo que la plantilla recorre
            'page_obj': page_obj,              # para la paginación del footer

            # Stats para la cabecera del perfil (opcionales en la plantilla)
            'stats_books': qs.count(),
            'stats_followers': subs_total,
            'stats_reads': reads_total,
            'stats_views': views_total,
        })
        return ctx

class ProfileEditView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user
