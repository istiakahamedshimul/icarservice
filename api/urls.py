from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'services', views.ServiceViewSet)
router.register(r'bookings', views.ServiceRequestViewSet)
router.register(r'reviews', views.ReviewViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('nearby-services/', views.nearby_services_api, name='nearby_services_api'),
    path('service-categories/', views.service_categories_api, name='service_categories_api'),
]