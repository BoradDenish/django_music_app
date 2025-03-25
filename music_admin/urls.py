from django.urls import path
from music_admin import views

urlpatterns = [
    # path("", views.index, name="index"),
    path('login', views.admin_login, name='admin_login'),
    path('logout', views.admin_logout, name='admin_logout'),
    path('dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('songs', views.admin_songs, name='admin_songs'),
    path('users', views.admin_users, name='admin_users'),

    path('user/delete/<int:id>', views.delete_user, name='delete_user'),

    # path('songs/edit/<int:song_id>', views.edit_song, name='edit_song'),
    # path('songs/delete/<int:song_id>', views.delete_song, name='delete_song'),
    # path('songs/add', views.add_song, name='add_song'),
]