from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from apps.library.models import (
    Category, Book, Chapter, BookSubscription, Comment
)
from apps.community.models import Post, Club
from apps.notifications.models import Notification

import random

User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with demo content for Librioo"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding demo data..."))

        # === Users ===
        writer1, _ = User.objects.get_or_create(
            username="writer1",
            defaults=dict(is_writer=True, bio="Escritor de ciencia ficción.")
        )
        writer1.set_password("1234"); writer1.save()

        writer2, _ = User.objects.get_or_create(
            username="writer2",
            defaults=dict(is_writer=True, bio="Narrador de fantasía épica.")
        )
        writer2.set_password("1234"); writer2.save()

        readers = []
        for i in range(1, 4):
            uname = f"reader{i}"
            u, _ = User.objects.get_or_create(
                username=uname,
                defaults=dict(is_writer=False, bio=f"Lector número {i}")
            )
            u.set_password("1234"); u.save()
            readers.append(u)

        # === Categories ===
        cat_sf, _ = Category.objects.get_or_create(name="Ciencia Ficción", slug="ciencia-ficcion")
        cat_fant, _ = Category.objects.get_or_create(name="Fantasía", slug="fantasia")

        # === Books ===
        book1, _ = Book.objects.get_or_create(
            title="La ciudad de acero",
            author=writer1,
            defaults=dict(
                synopsis="En un mundo post-apocalíptico, los últimos humanos viven en torres de acero.",
                category=cat_sf,
                status="serial",
                is_paid=False,
            )
        )

        book2, _ = Book.objects.get_or_create(
            title="El despertar del dragón",
            author=writer2,
            defaults=dict(
                synopsis="Una profecía milenaria anuncia el regreso de los dragones.",
                category=cat_fant,
                status="serial",
                is_paid=True,
                price_cents=499
            )
        )

        # === Chapters ===
        if book1.chapters.count() == 0:
            Chapter.objects.create(book=book1, number=1, title="El humo", content="El cielo estaba cubierto de humo...", status="published")
            Chapter.objects.create(book=book1, number=2, title="La torre", content="Desde lo alto se veía toda la ciudad...", status="published")

        if book2.chapters.count() == 0:
            Chapter.objects.create(book=book2, number=1, title="El huevo", content="En las montañas del norte, algo despertaba...", status="published")
            Chapter.objects.create(book=book2, number=2, title="La sombra", content="Los aldeanos sentían un miedo inexplicable...", status="draft")

        # === Subscriptions ===
        for r in readers:
            BookSubscription.objects.get_or_create(user=r, book=random.choice([book1, book2]))

        # === Comments (usar GFK) ===
        ct_chapter = ContentType.objects.get_for_model(Chapter)
        ch1 = book1.chapters.order_by('number').first()
        if ch1 and not Comment.objects.filter(content_type=ct_chapter, object_id=ch1.id).exists():
            Comment.objects.create(user=readers[0], content_type=ct_chapter, object_id=ch1.id, text="¡Me encanta este inicio!")
            Comment.objects.create(user=readers[1], content_type=ct_chapter, object_id=ch1.id, text="Quiero saber más...")

        # === Community ===
        if Post.objects.count() == 0:
            Post.objects.create(user=writer1, text="Estoy escribiendo un nuevo capítulo, ¿qué giro prefieren?")
            Post.objects.create(user=readers[0], text="Me uní a Librioo para descubrir nuevas historias :)")

        if Club.objects.count() == 0:
            Club.objects.create(name="Club de Ciencia Ficción", description="Discutimos lo último en sci-fi", is_premium=False)
            Club.objects.create(name="Amantes de la Fantasía", description="Dragones, magos y mundos mágicos", is_premium=True)

        # === Notificaciones demo ===
        ct_book = ContentType.objects.get_for_model(Book)
        if Notification.objects.count() == 0:
            if ch1:
                Notification.objects.create(
                    user=readers[0],
                    verb=f"Nuevo capítulo publicado: {ch1.title}",
                    content_type=ct_chapter,
                    object_id=ch1.id
                )
                Notification.objects.create(
                    user=writer1,
                    verb=f"{readers[0].username} comentó en tu capítulo",
                    content_type=ct_chapter,
                    object_id=ch1.id
                )

            Notification.objects.create(
                user=readers[1],
                verb=f"Comenzaste a seguir el libro {book2.title}",
                content_type=ct_book,
                object_id=book2.id
            )

        self.stdout.write(self.style.SUCCESS("Demo data created!"))
