from django.urls import path
from music_admin import views
from music_admin.view import authentication, users, songs

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path("", views.index, name="index"),
    path('login', authentication.admin_login, name='admin_login'),
    path('logout', authentication.admin_logout, name='admin_logout'),

    path('dashboard', views.admin_dashboard, name='admin_dashboard'),

    path('users', users.admin_users, name='admin_users'),
    path("add-user", users.add_user, name="add_user"),
    path('users/edit/<int:user_id>/', users.edit_user, name='edit_user'),
    path('user/delete/<int:id>', users.delete_user, name='delete_user'),

    path('video', views.admin_video, name='admin_video'),

    path('songs', songs.admin_songs, name='admin_songs'),
    path('songs/add', songs.add_song, name='add_song'),
    path('songs/edit/<int:song_id>', songs.edit_song, name='edit_song'),
    path('songs/delete/<int:song_id>', songs.delete_song, name='delete_song'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)