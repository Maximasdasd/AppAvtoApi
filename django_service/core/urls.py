from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name="home"),
    path('car/create_car', views.car_create, name='create_car'), 
]