"""
URL configuration for nuss_webapp project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin Interface
    path('admin/', admin.site.urls),

    # Main Students App (Dashboard, Payments, Events, etc.)
    path('', include('students.urls')),
]

# This serves MEDIA (receipts/profiles) and STATIC (css/js) during local development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Handling for potential 404/500 errors in the future (Optional)
admin.site.site_header = "NUSS Admin Portal"
admin.site.site_title = "NUSS Management"
admin.site.index_title = "Welcome to NUSS Admin HQ"