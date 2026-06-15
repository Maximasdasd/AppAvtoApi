from django.urls import path
from core.views.car import *
from core.views.client import *
from core.views.dashboard import *
from core.views.infome import *
from core.views.rentals import *
from core.views.repair import *
from core.views.staff import *

from . import fastapi_client

urlpatterns = [
    path('', fastapi_client.auto_login_to_fastapi, name="login"),
    path('dashboard', dashboard, name="home"),
    path('dashboard/car/create_car', car_create, name='create_car'),
    path('dashboard/rental/create_rental', rent_create, name='create_rental'),
    path('dashboard/repair/create_repair', repair_create, name='create_repair'),
    path('dashboard/repairs/complete_repair/<int:repair_id>', complete_repair, name='complete_repair'),
    path('dashboard/repairs/delete_repair_by_id/<int:repair_id>', cancel_repair, name='cancel_repair'),
    path('cars/', cars, name='cars'),
    path('cars/create/', cars_create, name='car_create'),
    path('cars/<int:pk>/', cars_detail, name='car_detail'),
    path('cars/<int:pk>/delete/', car_delete, name='car_delete'),
    path('clients/', clients, name='clients'),
    path('clients/create/', client_create, name='client_create'),
    path('clients/<int:pk>/', client_detail, name='client_detail'),
    # path('clients/delete/<int:pk>/', views.client_delete, name='client_delete'),
    path('rentals/', rentals, name='rentals'),
    path('rentals/create/', rentals_create, name='rentals_create'),
    path('rentals/<int:pk>/', rentals_detail, name='rentals_detail'),
    path('rentals/<int:pk>/complete', rental_complete, name='rental_complete'),
    path('rentals/<int:pk>/cancel', rental_cancel, name='rental_cancel'),
    path('repairs/', repairs, name='repairs'),
    path('repairs/create/', repairs_create, name='repairs_create'),
    path('repairs/<int:pk>/', repairs_detail, name='repairs_detail'),
    path('repairs/<int:pk>/complete', repair_complete, name='repair_complete'),
    path('repairs/<int:pk>/delete', repairs_delete, name='repairs_delete'),
    path('staff/', staff, name='staff'),
    path('staff/create/', staff_create, name='staff_create'),
    path('staff/<int:pk>', staff_detail, name='staff_detail'),
    path('infome/', infome, name='infome')
]