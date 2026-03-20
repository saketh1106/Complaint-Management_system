from django.contrib import admin
from django.urls import path, include

# 🔥 ADD THESE IMPORTS
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # connect complaints app
    path('', include('complaints.urls')),
]

# 🔥 THIS LINE IS MUST FOR FILES
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)