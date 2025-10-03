from django.contrib import admin
from .models import Quote, Category, Book, Collaboration, Chapter, BookSubscription, Comment, Reaction, Poll, PollOption, Vote, ChapterView, ReadingHistory, BookshelfItem

class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title','author','status','is_paid')
    list_filter = ('status','is_paid','category')
    search_fields = ('title','synopsis')
    inlines = [ChapterInline]

admin.site.register(Category)
admin.site.register(Collaboration)
admin.site.register(Chapter)
admin.site.register(BookSubscription)
admin.site.register(Comment)
admin.site.register(Reaction)
admin.site.register(Poll)
admin.site.register(PollOption)
admin.site.register(Vote)
admin.site.register(ChapterView)
admin.site.register(ReadingHistory)
admin.site.register(BookshelfItem)
admin.site.register(Quote)