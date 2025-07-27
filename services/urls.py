from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.service_list_view, name='list'),
    path('nearby/', views.nearby_services_view, name='nearby'),
    path('category/<int:category_id>/', views.services_by_category, name='by_category'),
    path('provider/<int:provider_id>/', views.provider_detail_view, name='provider_detail'),
    path('manage/', views.manage_services_view, name='manage'),
    path('add/', views.add_service_view, name='add'),
    path('edit/<int:service_id>/', views.edit_service_view, name='edit'),
    path('delete/<int:service_id>/', views.delete_service_view, name='delete'),
]