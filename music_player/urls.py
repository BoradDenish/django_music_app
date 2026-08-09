from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("signup", views.signup_view, name="signup"),
    path("home", views.home, name="home"),
    path("logout", views.logout_view, name="logout"),
    path("trending", views.trending, name="trending"),
    path("library", views.library, name="library"),
    path("favorites", views.favorites, name="favorites"),
    path("playlist", views.playlist, name="playlist"),
    path("profile", views.profile, name="profile"),
    path("music_library", views.music_library, name="music_library"),
    path("video_library", views.video_library, name="video_library"),
    path("upload_url", views.upload_url, name="upload_url"),

    # AJAX Endpoints
    path("toggle-favorite", views.toggle_favorite, name="toggle_favorite"),
    path("get-playlists", views.get_playlists, name="get_playlists"),
    path("add-to-playlist", views.add_to_playlist, name="add_to_playlist"),

    # Admin panel
    path("a/login", views.admin_login, name="admin_login"),
    path("a/logout", views.admin_logout, name="admin_logout"),
    path("a/dashboard", views.admin_dashboard, name="admin_dashboard"),
    path("a/users", views.admin_users, name="admin_users"),
    path("a/users/add", views.add_user, name="add_user"),
    path("a/users/edit/<int:user_id>", views.edit_user, name="edit_user"),
    path("a/user/delete/<int:user_id>", views.delete_user, name="delete_user"),
    path("a/songs", views.admin_songs, name="admin_songs"),
    path("a/songs/add", views.add_song, name="add_song"),
    path("a/songs/edit/<int:song_id>", views.edit_song, name="edit_song"),
    path("a/songs/delete/<int:song_id>", views.delete_song, name="delete_song"),
    path("a/videos", views.admin_video, name="admin_video"),
]
