from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name="home"),
    path('car/create_car', views.car_create, name='create_car'),
    path('rental/create_rental', views.rent_create, name='create_rental'),
    path('repair/create_repair', views.repair_create, name='create_repair'),
    path('repairs/complete_repair/<int:repair_id>', views.complete_repair, name='complete_repair'),
    path('repairs/delete_repair_by_id/<int:repair_id>', views.cancel_repair, name='cancel_repair')
]