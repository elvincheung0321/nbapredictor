from django.urls import path
from games import views

urlpatterns = [
    path("", views.game_listing, name='landing'),
]