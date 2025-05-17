from django.urls import path
from music_admin import views
from music_admin.view import authentication, users

urlpatterns = [
    # path("", views.index, name="index"),
    path('login', authentication.admin_login, name='admin_login'),
    path('logout', authentication.admin_logout, name='admin_logout'),

    path('dashboard', views.admin_dashboard, name='admin_dashboard'),

    path('users', users.admin_users, name='admin_users'),
    path("add-user", users.add_user, name="add_user"),
    path('user-edit', users.edit_user, name='edit_user'),
    path('user/delete/<int:id>', views.delete_user, name='delete_user'),

    path('songs', views.admin_songs, name='admin_songs'),
    path('video', views.admin_video, name='admin_video'),

    # path('songs/edit/<int:song_id>', views.edit_song, name='edit_song'),
    # path('songs/delete/<int:song_id>', views.delete_song, name='delete_song'),
    # path('songs/add', views.add_song, name='add_song'),
]