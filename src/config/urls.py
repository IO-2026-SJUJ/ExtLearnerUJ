"""URL configuration for ExtLearnerUJ project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin — tylko dla developerów
    path('', include('ExtLearnerUJ.urls')),
]

# W dev serwujemy media pliki bezpośrednio
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
