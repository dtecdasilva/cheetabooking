from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import scan_qr_code_view, process_qr_code_view
from .views import download_receipt


urlpatterns = [
    path('', views.index),
    path('index', views.index),
    path('book', views.book),
    path('bus', views.bus),
    path('trip', views.trip),
    path('about', views.about),
    path('agencies', views.agencies),
    path('dashboard', views.dashboard),
    path('search/', views.search_trips, name='search_trips'),
    path('addbus/', views.addbus, name='addbus'),
    path('addTrip/', views.addTrip, name='addTrip'),
    path('login_a/', views.login_a, name='login_a'),
    path('booking/', views.booking, name='booking'),
    path('scan_qr_code/', scan_qr_code_view, name='scan_qr_code'),
    path('process_qr_code/', process_qr_code_view, name='process_qr_code'),
    path('download-receipt/<str:unique_code>/', download_receipt, name='download_receipt'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)