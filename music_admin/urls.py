from django.urls import path
from music_admin import views

urlpatterns = [
    path("", views.index, name="index"),
    path('admin/login', views.admin_login, name='admin_login'),
    path('admin/logout', views.admin_logout, name='admin_logout'),
    path('admin/dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('admin/songs', views.admin_songs, name='admin_songs'),
    path('admin/users', views.admin_users, name='admin_users'),
]