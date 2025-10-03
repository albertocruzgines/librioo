from django.db import models
from django.conf import settings
from django.utils import timezone
from taggit.managers import TaggableManager
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = settings.AUTH_USER_MODEL

class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    slug = models.SlugField(max_length=140, unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

BOOK_STATUS = (
    ('draft','Borrador'),
    ('serial','En publicación (serializado)'),
    ('closed','Finalizado'),
)

class Book(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books')
    title = models.CharField(max_length=200)
    cover = models.ImageField(upload_to='covers/', blank=True, null=True)
    synopsis = models.TextField()
    prologue = models.TextField(blank=True)
    author_notes = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    subcategory = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_books')
    tags = TaggableManager(blank=True)
    status = models.CharField(max_length=10, choices=BOOK_STATUS, default='draft')
    is_paid = models.BooleanField(default=False)
    price_cents = models.PositiveIntegerField(default=0)
    downloadable_pdf = models.FileField(upload_to='books/pdf/', blank=True, null=True)
    downloadable_epub = models.FileField(upload_to='books/epub/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

COLLAB_ROLE = (
    ('coauthor','Co-autor'),
    ('editor','Corrector/Editor'),
    ('illustrator','Ilustrador'),
)

class Collaboration(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='collaborations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collaborations')
    role = models.CharField(max_length=20, choices=COLLAB_ROLE)
    invited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('book','user','role')

CHAPTER_STATUS = (
    ('draft','Borrador'),
    ('scheduled','Programado'),
    ('published','Publicado'),
)

class Chapter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    number = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=10, choices=CHAPTER_STATUS, default='draft')
    publish_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('book','number')
        ordering = ['number']

    @property
    def is_visible(self):
        if self.status == 'published':
            return True
        if self.status == 'scheduled' and self.publish_at and self.publish_at <= timezone.now():
            return True
        return False

class BookSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_subscriptions')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='subscribers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user','book')

class ChapterView(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='views')
    created_at = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type','object_id')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_quote = models.BooleanField(default=False) 

class Reaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type','object_id')
    kind = models.CharField(max_length=20, default='like')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user','content_type','object_id','kind')

class Poll(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='polls')
    question = models.CharField(max_length=240)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=140)
    votes = models.ManyToManyField(User, through='Vote', related_name='poll_votes')

class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('poll','user')

class ReadingHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_history')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    last_chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

class BookshelfItem(models.Model):
    STATUS = (('favorite','Favorito'),('pending','Pendiente'),('reading','Leyendo'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookshelf')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user','book')

class Quote(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='quotes')
    chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quotes')
    text = models.CharField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (self.text[:50] + '…') if len(self.text) > 50 else self.text

class ChapterRevision(models.Model):
    chapter = models.ForeignKey('Chapter', on_delete=models.CASCADE, related_name='revisions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    # Si tu Chapter no tiene content_html, no pasa nada; lo dejamos solo en la revisión.
    content_html = models.TextField(blank=True)
    is_autosave = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Rev {self.id} · {self.chapter_id} · {self.user}"
