from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve # <--- Add this import
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('complaints.urls')),
]

# This block handles files even when DEBUG is False
urlpatterns += [
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)