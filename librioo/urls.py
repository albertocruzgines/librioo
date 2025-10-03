from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from apps.library.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('user/', include(('apps.accounts.urls', 'accounts'), namespace='accounts')),
    path('', HomeView.as_view(), name='home'),
    path('library/', include('apps.library.urls')),
    path('community/', include('apps.community.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('payments/', include('apps.payments.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
