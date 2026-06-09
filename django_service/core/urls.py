from django.urls import path
from . import views
from . import fastapi_client

urlpatterns = [
    path('', fastapi_client.auto_login_to_fastapi, name="login"),
    path('dashboard', views.dashboard, name="home"),
    path('dashboard/car/create_car', views.car_create, name='create_car'),
    path('dashboard/rental/create_rental', views.rent_create, name='create_rental'),
    path('dashboard/repair/create_repair', views.repair_create, name='create_repair'),
    path('dashboard/repairs/complete_repair/<int:repair_id>', views.complete_repair, name='complete_repair'),
    path('dashboard/repairs/delete_repair_by_id/<int:repair_id>', views.cancel_repair, name='cancel_repair'),
    path('cars/', views.cars, name='cars'),
    path('cars/create/', views.cars_create, name='car_create'),
    path('cars/<int:pk>/', views.cars_detail, name='car_detail'),
    path('cars/<int:pk>/delete/', views.car_delete, name='car_delete'),
    path('clients/', views.clients, name='clients'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    # path('clients/delete/<int:pk>/', views.client_delete, name='client_delete'),
    path('rentals/', views.rentals, name='rentals'),
    path('rentals/create/', views.rentals_create, name='rentals_create'),
    path('rentals/<int:pk>/', views.rentals_detail, name='rentals_detail'),
    path('rentals/<int:pk>/complete', views.rental_complete, name='rental_complete'),
    path('rentals/<int:pk>/cancel', views.rental_cancel, name='rental_cancel'),
    path('repairs/', views.repairs, name='repairs'),
    path('repairs/create/', views.repairs_create, name='repairs_create'),
    path('repairs/<int:pk>/', views.repairs_detail, name='repairs_detail'),
    path('repairs/<int:pk>/complete', views.repair_complete, name='repair_complete'),
    path('repairs/<int:pk>/delete', views.repairs_delete, name='repairs_delete'),
    path('staff/', views.staff, name='staff'),
    path('staff/create/', views.staff_create, name='staff_create'),
    path('staff/<int:pk>', views.staff_detail, name='staff_detail'),
    path('infome/', views.infome, name='infome')
]