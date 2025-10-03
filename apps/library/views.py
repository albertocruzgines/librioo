from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, Max
from .models import Quote,Book, Collaboration, ReadingHistory, Chapter, Comment, Reaction, Poll, PollOption, Vote, BookSubscription, ChapterView, BookshelfItem, Category
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import BookshelfItem, ReadingHistory
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.db.models import BooleanField, Case, When, Value
from django.contrib.auth import get_user_model
from django.apps import apps as django_apps
from .forms import ChapterForm


User = get_user_model()


ALLOWED_SHELF_STATUSES = {'favorite','pending','reading'}
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q, Max
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from apps.library.models import (
    Book, Chapter, Category, Poll, Comment,
    ReadingHistory, BookshelfItem, BookSubscription
)

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        # 1) Destacados
        featured = (
            Book.objects.select_related('author', 'category')
            .annotate(
                latest_published_at=Max(
                    'chapters__publish_at',
                    filter=Q(chapters__status='published')
                )
            )
            .order_by('-latest_published_at', '-updated_at')[:6]
        )

        # 2) Tendencias
        trending = (
            Book.objects.select_related('author', 'category')
            .annotate(
                recent_views=Count(
                    'chapters__views',
                    filter=Q(chapters__views__created_at__gte=week_ago),
                    distinct=True
                ),
                num_subs=Count('subscribers', distinct=True),
                num_chapters=Count('chapters', distinct=True),
            )
            .order_by('-recent_views', '-num_subs', '-num_chapters', '-updated_at')[:12]
        )

        # 3) Capítulos frescos (7 días)
        fresh_chapters = (
            Chapter.objects
            .filter(status='published', publish_at__isnull=False,
                    publish_at__lte=now, publish_at__gte=week_ago)
            .select_related('book', 'book__author')
            .order_by('-publish_at')[:12]
        )

        # 4) Categorías top
        top_categories = (
            Category.objects
            .annotate(
                books_count=Count('books', distinct=True),
                recent_views=Count(
                    'books__chapters__views',
                    filter=Q(books__chapters__views__created_at__gte=week_ago),
                    distinct=True
                )
            )
            .order_by('-recent_views', '-books_count', 'name')[:12]
        )

        # 5) Picks editoriales
        editors_picks = (
            Book.objects.filter(status__in=['serial', 'closed'])
            .select_related('author', 'category')
            .annotate(
                latest_published_at=Max(
                    'chapters__publish_at',
                    filter=Q(chapters__status='published')
                ),
                num_subs=Count('subscribers', distinct=True),
            )
            .order_by('-num_subs', '-latest_published_at', '-updated_at')[:8]
        )

        # 6) Encuestas activas
        active_polls = (
            Poll.objects.filter(is_active=True)
            .select_related('chapter', 'chapter__book', 'chapter__book__author')
            .annotate(total_votes=Count('options__votes', distinct=True))
            .order_by('-created_at')[:6]
        )

        # 7) Reseñas recientes (comments raíz sobre Book)
        ct_book = ContentType.objects.get_for_model(Book)
        recent_reviews = (
            Comment.objects.filter(content_type=ct_book, parent__isnull=True)
            .select_related('user')
            .order_by('-created_at')[:8]
        )

        continue_reading = []
        recommendations = []
        new_for_you = []

        if self.request.user.is_authenticated:
            user = self.request.user

            # 8) Seguir leyendo
            continue_reading = (
                ReadingHistory.objects.filter(user=user)
                .select_related('book', 'book__author', 'last_chapter')
                .order_by('-updated_at')[:8]
            )

            # Categorías favoritas del usuario
            fav_cat_ids = set(
                BookshelfItem.objects.filter(user=user)
                .values_list('book__category_id', flat=True)
            ) | set(
                ReadingHistory.objects.filter(user=user)
                .values_list('book__category_id', flat=True)
            ) | set(
                BookSubscription.objects.filter(user=user)
                .values_list('book__category_id', flat=True)
            )
            fav_cat_ids = {cid for cid in fav_cat_ids if cid}

            # 9) Recomendaciones
            base_rec = (
                Book.objects.select_related('author', 'category')
                .annotate(
                    followers=Count('subscribers', distinct=True),
                    latest_published_at=Max(
                        'chapters__publish_at',
                        filter=Q(chapters__status='published')
                    ),
                )
            )
            if fav_cat_ids:
                base_rec = base_rec.filter(category_id__in=list(fav_cat_ids))

            recommendations = (
                base_rec.exclude(author_id=user.id)
                .exclude(subscribers__user_id=user.id)
                .order_by('-followers', '-latest_published_at', '-updated_at')
                .distinct()[:12]
            )

            # 10) Novedades para ti
            new_for_you = (
                Book.objects.select_related('author', 'category')
                .annotate(
                    latest_new=Max(
                        'chapters__publish_at',
                        filter=Q(
                            chapters__status='published',
                            chapters__publish_at__gte=week_ago,
                            chapters__publish_at__lte=now,
                        )
                    )
                )
                .filter(latest_new__isnull=False)
                .filter(
                    Q(subscribers__user_id=user.id) |
                    Q(category_id__in=list(fav_cat_ids) if fav_cat_ids else [])
                )
                .exclude(author_id=user.id)
                .order_by('-latest_new')
                .distinct()[:12]
            )
        else:
            # Novedades generales
            new_for_you = (
                Book.objects.select_related('author', 'category')
                .annotate(
                    latest_new=Max(
                        'chapters__publish_at',
                        filter=Q(
                            chapters__status='published',
                            chapters__publish_at__gte=week_ago,
                            chapters__publish_at__lte=now,
                        )
                    )
                )
                .filter(latest_new__isnull=False)
                .order_by('-latest_new')[:12]
            )

        # 11) Autores destacados (User anotado) -> avatar accesible como a.avatar.url
        User = get_user_model()
        top_authors = (
            User.objects
            .annotate(
                books_count=Count('books', distinct=True),
                followers_count=Count('books__subscribers__user', distinct=True),
                views7d=Count(
                    'books__chapters__views',
                    filter=Q(books__chapters__views__created_at__gte=week_ago),
                    distinct=True
                ),
            )
            .filter(books_count__gt=0)
            .order_by('-views7d', '-followers_count', '-books_count', 'username')[:10]
            .only('id', 'username', 'avatar')
        )

        ctx.update({
            'now': now,
            'week_ago': week_ago,
            'featured': featured,
            'trending': trending,
            'fresh_chapters': fresh_chapters,
            'top_categories': top_categories,
            'editors_picks': editors_picks,
            'active_polls': active_polls,
            'recent_reviews': recent_reviews,
            'continue_reading': continue_reading,
            'recommendations': recommendations,
            'new_for_you': new_for_you,
            'top_authors': top_authors,  # queryset de User con avatar listo
        })
        return ctx


class LibraryHomeView(TemplateView):
    template_name = 'library/home.html'

class BookListView(ListView):
    model = Book
    template_name = 'library/book_list.html'
    paginate_by = 12

    def get_queryset(self):
        qs = Book.objects.all().select_related('author','category','subcategory')
        state = self.request.GET.get('state')
        cat = self.request.GET.get('cat')
        if state in ('serial','closed','draft'):
            qs = qs.filter(status=state)
        if cat:
            qs = qs.filter(category__slug=cat)
        return qs.order_by('-created_at')

class BookDetailView(DetailView):
    model = Book
    template_name = 'library/book_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        request = self.request
        book = self.object

        now = timezone.now()
        week_ago = now - timedelta(days=7)

        can_read = not book.is_paid  # por defecto, gratis -> se puede leer

        if request.user.is_authenticated:
            if (
                request.user.is_superuser
                or request.user == book.author
                or Collaboration.objects.filter(book=book, user=request.user).exists()
            ):
                can_read = True
            # TODO: aquí podrías añadir la verificación real de compra si ya tienes el modelo
            # from apps.payments.models import BookPurchase
            # can_read = can_read or BookPurchase.objects.filter(user=request.user, book=book, status='paid').exists()

        ctx['can_read'] = can_read
        # ✅ Capítulos con flag is_new (últimos 7 días)
        chapters_qs = (
            Chapter.objects
            .filter(book=book)
            .annotate(
                is_new=Case(
                    When(publish_at__isnull=False, publish_at__gte=week_ago, publish_at__lte=now, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
            .order_by('number')
        )
        ctx['chapters'] = chapters_qs
        ctx['week_ago'] = week_ago
        ctx['now'] = now

        # Suscripción / estantería / permisos
        if request.user.is_authenticated:
            ctx['subscribed'] = BookSubscription.objects.filter(user=request.user, book=book).exists()
            ctx['shelf_item'] = BookshelfItem.objects.filter(user=request.user, book=book).first()
            ctx['can_curate'] = (
                request.user.is_superuser
                or request.user == book.author
                or Collaboration.objects.filter(book=book, user=request.user).exists()
            )
        else:
            ctx['subscribed'] = False
            ctx['shelf_item'] = None
            ctx['can_curate'] = False

        # Reseñas (igual)
        ct_book = ContentType.objects.get_for_model(Book)
        ctx['reviews'] = (
            Comment.objects
            .filter(content_type=ct_book, object_id=book.id, parent__isnull=True)
            .select_related('user')
            .order_by('-created_at')
        )

        # Citas (igual)
        ct_chapter = ContentType.objects.get_for_model(Chapter)
        chapter_ids = Chapter.objects.filter(book=book).values('id')
        ctx['quotes'] = (
            Comment.objects
            .filter(content_type=ct_chapter, object_id__in=chapter_ids, is_quote=True, parent__isnull=True)
            .select_related('user')
            .order_by('-created_at')[:50]
        )

        # Métricas (usa el mismo criterio que is_new para contar)
        ctx['followers'] = BookSubscription.objects.filter(book=book).count()
        ctx['favorites'] = BookshelfItem.objects.filter(book=book, status='favorite').count()
        ctx['total_chapters'] = chapters_qs.count()
        ctx['new_chapters_count'] = chapters_qs.filter(is_new=True).count()

        return ctx

@method_decorator(login_required, name='dispatch')
class BookCreateView(CreateView):
    model = Book
    fields = ['title','cover','synopsis','prologue','author_notes','category','subcategory','status','is_paid','price_cents','downloadable_pdf','downloadable_epub']
    template_name = 'library/book_form.html'
    success_url = reverse_lazy('library:book_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

@login_required
def subscribe_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    sub, created = BookSubscription.objects.get_or_create(user=request.user, book=book)
    if not created:
        sub.delete()
    return redirect('library:book_detail', pk=pk)

class ChapterCreateView(CreateView):
    model = Chapter
    form_class = ChapterForm
    template_name = "library/chapter_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.book = get_object_or_404(Book, pk=self.kwargs.get("pk"))
        user = request.user
        is_author = (self.book.author_id == user.id)
        is_collab = Collaboration.objects.filter(book=self.book, user=user).exists()
        if not (user.is_superuser or is_author or is_collab):
            return HttpResponseForbidden("No tienes permisos para crear capítulos en este libro.")
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        last = Chapter.objects.filter(book=self.book).order_by("-number").first()
        initial["number"] = (last.number + 1) if last and last.number is not None else 1
        return initial

    def form_valid(self, form):
        form.instance.book = self.book
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["book"] = self.book
        return ctx

    def get_success_url(self):
        return reverse_lazy("library:book_detail", kwargs={"pk": self.book.id})

class ChapterReadView(DetailView):
    model = Chapter
    template_name = 'library/chapter_read.html'
    context_object_name = 'chapter'

    def _can_curate(self, user, book):
        if not user.is_authenticated:
            return False
        return (
            user.is_superuser
            or user == book.author
            or Collaboration.objects.filter(book=book, user=user).exists()
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user.is_authenticated:
            ChapterView.objects.create(user=request.user, chapter=self.object)
            BookshelfItem.objects.get_or_create(
                user=request.user, book=self.object.book, defaults={'status': 'reading'}
            )
            ReadingHistory.objects.update_or_create(
                user=request.user, book=self.object.book,
                defaults={'last_chapter': self.object}
            )
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        from django.contrib.contenttypes.models import ContentType
        ctx = super().get_context_data(**kwargs)
        chapter = self.object
        book = chapter.book
        user = self.request.user

        # normaliza nombre para el template
        setattr(chapter, 'published_at', getattr(chapter, 'publish_at', None))

        # vistas
        views_count = ChapterView.objects.filter(chapter=chapter).count()
        ctx['views_count'] = views_count

        # comentarios (raíz + hijos)
        ct_chapter = ContentType.objects.get_for_model(Chapter)
        all_comments = list(
            Comment.objects
            .filter(content_type=ct_chapter, object_id=chapter.id)
            .select_related('user')
            .order_by('created_at')
        )
        roots = [c for c in all_comments if c.parent_id is None]
        children_map = {}
        for c in all_comments:
            if c.parent_id:
                children_map.setdefault(c.parent_id, []).append(c)
        for r in roots:
            setattr(r, 'children', children_map.get(r.id, []))
        comments_count = len(all_comments)

        # tiempo de lectura
        raw = chapter.content_html if getattr(chapter, 'content_html', None) else (chapter.content or '')
        words = len((raw or '').split())
        read_time = max(1, round(words / 200))

        # prev/next
        if chapter.number is not None:
            prev_chapter = Chapter.objects.filter(book=book, number__lt=chapter.number).order_by('-number').first()
            next_chapter = Chapter.objects.filter(book=book, number__gt=chapter.number).order_by('number').first()
        else:
            prev_chapter = Chapter.objects.filter(book=book, id__lt=chapter.id).order_by('-id').first()
            next_chapter = Chapter.objects.filter(book=book, id__gt=chapter.id).order_by('id').first()

        # relacionados
        related_chapters = Chapter.objects.filter(book=book).exclude(id=chapter.id).order_by('-publish_at', '-updated_at')[:8]
        related_books = (
            Book.objects.filter(category=book.category).exclude(id=book.id)
            .select_related('author', 'category').order_by('-updated_at')[:4]
            if book.category_id else []
        )

        # subs / estantería
        is_subscribed = False
        can_subscribe = False
        can_shelve = False
        if user.is_authenticated:
            is_subscribed = BookSubscription.objects.filter(user=user, book=book).exists()
            can_subscribe = (user != book.author) or user.is_superuser
            can_shelve = True

        ctx.update({
            'comments': roots,                 # cada root trae .children
            'comments_count': comments_count,  # total (incluye respuestas)
            'read_time': read_time,
            'prev_chapter': prev_chapter,
            'next_chapter': next_chapter,
            'related_chapters': related_chapters,
            'related_books': related_books,
            'popular_tags': [],
            'is_subscribed': is_subscribed,
            'can_subscribe': can_subscribe,
            'can_shelve': can_shelve,
            'can_curate': self._can_curate(user, book),
        })
        return ctx


def _can_curate_book(user, book):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user == book.author or Collaboration.objects.filter(book=book, user=user).exists()

@login_required
@require_POST
def create_comment(request, pk):
    chapter = get_object_or_404(Chapter, pk=pk)
    text = (request.POST.get('text') or '').strip()
    mark_quote = request.POST.get('is_quote') == 'on'
    if not text:
        return redirect('library:chapter_read', pk=pk)

    is_quote = False
    if mark_quote and _can_curate_book(request.user, chapter.book):
        is_quote = True

    Comment.objects.create(
        user=request.user,
        content_type=ContentType.objects.get_for_model(Chapter),
        object_id=chapter.id,
        text=text,
        is_quote=is_quote,
    )
    return redirect('library:chapter_read', pk=pk)

@login_required
@require_POST
def toggle_comment_quote(request, pk):
    c = get_object_or_404(Comment, pk=pk)
    # Solo se admiten citas sobre capítulos
    ct_chapter = ContentType.objects.get_for_model(Chapter)
    if c.content_type_id != ct_chapter.id:
        return HttpResponseForbidden('Solo se pueden marcar citas en comentarios de capítulos.')
    chapter = Chapter.objects.get(pk=c.object_id)
    if not _can_curate_book(request.user, chapter.book):
        return HttpResponseForbidden('No tienes permiso para marcar citas en este libro.')
    c.is_quote = not c.is_quote
    c.save(update_fields=['is_quote'])
    return redirect('library:chapter_read', pk=chapter.id)
@login_required
@require_POST
def reply_comment(request, pk):
    parent = get_object_or_404(Comment, pk=pk)
    text = (request.POST.get('text') or '').strip()
    if not text:
        # vuelve al capítulo del hilo
        target_id = parent.object_id
        return redirect('library:chapter_read', pk=target_id)
    Comment.objects.create(
        user=request.user,
        content_type=parent.content_type,
        object_id=parent.object_id,
        text=text,
        parent=parent
    )
    return redirect('library:chapter_read', pk=parent.object_id)

@login_required
def react_toggle(request, model, object_id, kind):
    model_map = {{
        'chapter': Chapter,
        'book': Book,
        'comment': Comment,
        'quote': Quote,
    }}
    Model = model_map.get(model)
    if not Model:
        return HttpResponseForbidden('Modelo no permitido')
    obj = get_object_or_404(Model, pk=object_id)
    ct = ContentType.objects.get_for_model(Model)
    existing = Reaction.objects.filter(user=request.user, content_type=ct, object_id=obj.id, kind=kind)
    if existing.exists():
        existing.delete()
    else:
        Reaction.objects.create(user=request.user, content_type=ct, object_id=obj.id, kind=kind)
    return redirect(request.META.get('HTTP_REFERER','/'))

@login_required
def vote_poll(request, poll_id, option_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    option = get_object_or_404(PollOption, pk=option_id, poll=poll)
    Vote.objects.update_or_create(poll=poll, user=request.user, defaults={{'option': option}})
    return redirect(request.META.get('HTTP_REFERER','/'))

@method_decorator(login_required, name='dispatch')
class WriterDashboardView(TemplateView):
    template_name = 'library/writer_dashboard.html'

    def get_context_data(self, **kwargs):
        from django.db.models import Count, OuterRef, Subquery, IntegerField
        from django.contrib.contenttypes.models import ContentType
        from .models import Book, ChapterView, Chapter, Comment, Reaction

        ctx = super().get_context_data(**kwargs)
        me = self.request.user

        # Subqueries para lecturas totales por libro
        views_sq = (
            ChapterView.objects
            .filter(chapter__book=OuterRef('pk'))
            .values('chapter__book')
            .annotate(c=Count('*'))
            .values('c')[:1]
        )

        # Para comentarios y reacciones (GFK a Chapter) usamos subqueries con IN sobre capítulos del libro.
        ct_chapter = ContentType.objects.get_for_model(Chapter)

        comments_sq = (
            Comment.objects
            .filter(content_type=ct_chapter, object_id__in=Chapter.objects.filter(book=OuterRef('pk')).values('id'))
            .values('object_id')
            .annotate(c=Count('*'))
            .values('c')[:1]
        )

        likes_sq = (
            Reaction.objects
            .filter(content_type=ct_chapter, object_id__in=Chapter.objects.filter(book=OuterRef('pk')).values('id'), kind='like')
            .values('object_id')
            .annotate(c=Count('*'))
            .values('c')[:1]
        )

        books = (
            Book.objects
            .filter(author=me)
            .annotate(
                reads=Subquery(views_sq, output_field=IntegerField()),
                comments=Subquery(comments_sq, output_field=IntegerField()),
                likes=Subquery(likes_sq, output_field=IntegerField()),
                num_chapters=Count('chapters', distinct=True),
                subs=Count('subscribers', distinct=True),
            )
            .order_by('-created_at')
        )

        # fallback a 0 si las subqueries vienen None
        for b in books:
            b.reads = b.reads or 0
            b.comments = b.comments or 0
            b.likes = b.likes or 0

        ctx['books'] = books
        return ctx

class DiscoverView(TemplateView):
    template_name = 'library/discover.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        trending = (
            Book.objects
            .select_related('author','category','subcategory')
            .annotate(
                num_views=Count('chapters__views', distinct=True),
                num_subs=Count('subscribers', distinct=True),
                num_chapters=Count('chapters', distinct=True),
                latest_published_at=Max(
                    'chapters__publish_at',
                    filter=Q(chapters__status='published')
                ),
                new_chapters=Count(
                    'chapters',
                    filter=Q(chapters__status='published', chapters__publish_at__gte=week_ago),
                    distinct=True
                ),
            )
            .order_by('-num_views', '-num_subs', '-num_chapters')[:12]
        )

        ctx['trending'] = trending
        ctx['week_ago'] = week_ago
        ctx['now'] = now
        return ctx


@method_decorator(login_required, name='dispatch')
class ChapterUpdateView(UpdateView):
    model = Chapter
    form_class = ChapterForm
    template_name = "library/chapter_form.html"

    def get_success_url(self):
        return reverse_lazy("library:chapter_read", kwargs={"pk": self.object.id})

    def dispatch(self, request, *args, **kwargs):
        # Permisos: autor del libro o colaborador (coautor/editor/ilustrador)
        obj = self.get_object()
        user = request.user
        is_author = (obj.book.author_id == user.id)
        is_collab = Collaboration.objects.filter(book=obj.book, user=user).exists()
        if not (is_author or is_collab or user.is_superuser):
            return HttpResponseForbidden('No tienes permisos para editar este capítulo.')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('library:book_detail', kwargs={'pk': self.object.book_id})
class ShelfView(LoginRequiredMixin, TemplateView):
    template_name = 'library/shelf.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        week_ago = timezone.now() - timedelta(days=7)

        # 🔧 Usa campos reales: status + publish_at
        ctx['shelf'] = (
            BookshelfItem.objects
            .filter(user=user)
            .select_related('book', 'book__author', 'book__category')
            .annotate(
                            # última publicación de capítulo (solo publicados)
                            latest_published_at=Max(
                                'book__chapters__publish_at',
                                filter=Q(book__chapters__status='published')
                            ),
                            # capítulos nuevos en los últimos 7 días
                            new_chapters=Count(
                                'book__chapters',
                                filter=Q(
                                    book__chapters__status='published',
                                    book__chapters__publish_at__gte=week_ago
                                ),
                                distinct=True
                            ),
                            chapters_count=Count('book__chapters', distinct=True),
                            followers_count=Count('book__subscribers', distinct=True),
                        )
            .order_by('status', '-created_at')
        )

        ctx['history'] = (
            ReadingHistory.objects
            .filter(user=user)
            .select_related('book', 'last_chapter')
            .order_by('-updated_at')[:100]
        )

        subs_qs = BookSubscription.objects.filter(user=user)
        ctx['subs'] = subs_qs.select_related('book', 'book__author').order_by('-created_at')
        ctx['subs_ids'] = list(subs_qs.values_list('book_id', flat=True))

        ctx['week_ago'] = week_ago
        ctx['now'] = timezone.now()
        return ctx
        
@login_required
def subscribe_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    sub, created = BookSubscription.objects.get_or_create(user=request.user, book=book)
    if created:
        BookshelfItem.objects.get_or_create(user=request.user, book=book, defaults={'status': 'reading'})
    else:
        # opcional: quitar de estantería al dejar de seguir
        # BookshelfItem.objects.filter(user=request.user, book=book).delete()
        sub.delete()
    return redirect('library:book_detail', pk=pk)

@login_required
@require_POST
def shelf_set_status(request, book_id, status):
    if status not in ALLOWED_SHELF_STATUSES:
        return HttpResponseForbidden('Estado no válido')
    book = get_object_or_404(Book, pk=book_id)
    item, _ = BookshelfItem.objects.get_or_create(user=request.user, book=book)
    item.status = status
    item.save(update_fields=['status'])
    return redirect('library:book_detail', pk=book_id)

@login_required
@require_POST
def shelf_set_status(request, book_id, status):
    if status not in ALLOWED_SHELF_STATUSES:
        return HttpResponseForbidden('Estado no válido')
    book = get_object_or_404(Book, pk=book_id)
    item, _ = BookshelfItem.objects.get_or_create(user=request.user, book=book)
    item.status = status
    item.save(update_fields=['status'])
    return redirect('library:shelf')

@login_required
@require_POST
def shelf_remove(request, book_id):
    BookshelfItem.objects.filter(user=request.user, book_id=book_id).delete()
    return redirect('library:shelf')


@method_decorator(login_required, name='dispatch')
class BookUpdateView(UpdateView):
    model = Book
    fields = ['title','cover','synopsis','prologue','author_notes',
              'category','subcategory','status','is_paid','price_cents',
              'downloadable_pdf','downloadable_epub']
    template_name = 'library/book_form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        user = request.user
        is_author = (obj.author_id == user.id)
        is_collab = Collaboration.objects.filter(book=obj, user=user).exists()
        if not (is_author or is_collab or user.is_superuser):
            return HttpResponseForbidden('No tienes permisos para editar este libro.')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('library:book_detail', kwargs={'pk': self.object.pk})

# Crear reseña (Comment sobre Book)
@login_required
@require_POST
def create_book_review(request, pk):
    book = get_object_or_404(Book, pk=pk)
    text = request.POST.get('text', '').strip()
    if text:
        ct = ContentType.objects.get_for_model(Book)
        Comment.objects.create(user=request.user, content_type=ct, object_id=book.id, text=text)
    return redirect('library:book_detail', pk=pk)

# Crear cita (Quote)
@login_required
@require_POST
def create_quote(request, pk):
    book = get_object_or_404(Book, pk=pk)
    text = request.POST.get('text', '').strip()
    chapter_id = request.POST.get('chapter') or None
    if text:
        ch = None
        if chapter_id:
            try:
                ch = Chapter.objects.get(pk=chapter_id, book=book)
            except Chapter.DoesNotExist:
                ch = None
        Quote.objects.create(book=book, chapter=ch, user=request.user, text=text)
    return redirect('library:book_detail', pk=pk)

from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.timezone import now

from .models import Chapter, ChapterRevision, Collaboration

def _can_edit_chapter(user, chapter):
    return (
        user.is_authenticated and (
            user.is_superuser or
            chapter.book.author_id == user.id or
            Collaboration.objects.filter(book=chapter.book, user=user).exists()
        )
    )

@login_required
@require_POST
def chapter_autosave(request, pk):
    ch = get_object_or_404(Chapter, pk=pk)
    if not _can_edit_chapter(request.user, ch):
        return HttpResponseForbidden('No puedes editar este capítulo.')

    title = request.POST.get('title', ch.title or '')
    content = request.POST.get('content', '')
    content_html = request.POST.get('content_html', '')

    ChapterRevision.objects.create(
        chapter=ch, user=request.user, title=title,
        content=content, content_html=content_html, is_autosave=True
    )

    # Actualiza el capítulo si no está publicado (opcional)
    if getattr(ch, 'status', '') != 'published':
        upd = []
        if title and title != (ch.title or ''):
            ch.title = title; upd.append('title')
        if content and content != (ch.content or ''):
            ch.content = content; upd.append('content')
        if hasattr(ch, 'content_html') and content_html and content_html != (getattr(ch,'content_html', '') or ''):
            ch.content_html = content_html; upd.append('content_html')
        if upd: ch.save(update_fields=upd)

    # Limita autosaves a 50
    extra_ids = list(ch.revisions.filter(is_autosave=True).values_list('id', flat=True)[50:])
    if extra_ids: ChapterRevision.objects.filter(id__in=extra_ids).delete()

    return JsonResponse({'ok': True, 'saved_at': now().isoformat()})

@login_required
def chapter_revisions(request, pk):
    ch = get_object_or_404(Chapter, pk=pk)
    if not _can_edit_chapter(request.user, ch):
        return HttpResponseForbidden()
    revs = ch.revisions.select_related('user')[:50]
    data = [
        {'id': r.id, 'user': r.user.username, 'autosave': r.is_autosave,
         'created_at': r.created_at.strftime('%Y-%m-%d %H:%M'), 'title': (r.title or '')[:160]}
        for r in revs
    ]
    return JsonResponse({'revisions': data})

@login_required
@require_POST
def chapter_revision_restore(request, pk, rev_id):
    ch = get_object_or_404(Chapter, pk=pk)
    if not _can_edit_chapter(request.user, ch):
        return HttpResponseForbidden()
    r = get_object_or_404(ChapterRevision, pk=rev_id, chapter=ch)

    # Guarda backup del estado actual como revisión manual
    ChapterRevision.objects.create(
        chapter=ch, user=request.user, title=ch.title or '',
        content=ch.content or '', content_html=getattr(ch, 'content_html', '') or '',
        is_autosave=False
    )

    ch.title = r.title or ch.title
    ch.content = r.content or ch.content
    if hasattr(ch, 'content_html'):
        ch.content_html = r.content_html or getattr(ch, 'content_html', '')
    ch.save()
    return JsonResponse({'ok': True})

@login_required
@require_POST
def chapter_save_version(request, pk):
    ch = get_object_or_404(Chapter, pk=pk)
    if not _can_edit_chapter(request.user, ch):
        return HttpResponseForbidden()
    ChapterRevision.objects.create(
        chapter=ch, user=request.user,
        title=request.POST.get('title', ch.title or ''),
        content=request.POST.get('content', ch.content or ''),
        content_html=request.POST.get('content', ''),
        is_autosave=False
    )
    return JsonResponse({'ok': True})

@login_required
@require_POST
def richtext_image_upload(request):
    f = request.FILES.get('upload')
    if not f:
        return JsonResponse({'error': 'No file'}, status=400)
    # Aquí puedes validar tipo/tamaño si quieres
    path = default_storage.save(f"rich/{request.user.id}/{f.name}", ContentFile(f.read()))
    return JsonResponse({'url': default_storage.url(path)})
