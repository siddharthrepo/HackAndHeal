from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('auth_app.urls')),
    path('consultation/', include('consultation_app.urls')),
    path('payment/', include('payment_app.urls')),
    path('chat/', include('chat_app.urls')),
    path('transcription/', include('transcription_app.urls')),
    path('', include('consultation_app.urls')),  # Landing page is part of consultation app
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
