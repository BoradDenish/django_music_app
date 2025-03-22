from django.urls import path
from music_admin import views

urlpatterns = [
    path("", views.index, name="index"),
    path('login', views.admin_login, name='admin_login'),
    path('logout', views.admin_logout, name='admin_logout'),
    path('dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('songs', views.admin_songs, name='admin_songs'),
    path('users', views.admin_users, name='admin_users'),
]