from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.booking_list_view, name='list'),
    path('create/', views.create_booking_view, name='create'),
    path('<int:booking_id>/', views.booking_detail_view, name='detail'),
    path('<int:booking_id>/update/', views.update_booking_status, name='update_status'),
    path('<int:booking_id>/cancel/', views.cancel_booking_view, name='cancel'),
    path('provider/requests/', views.provider_requests_view, name='provider_requests'),
    path('request/<int:request_id>/accept/', views.accept_request_view, name='accept_request'),
    path('request/<int:request_id>/reject/', views.reject_request_view, name='reject_request'),
]