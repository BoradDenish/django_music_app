from django.urls import path
from . import views

urlpatterns = [
    # Public & Auth
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("signup", views.signup_view, name="signup"),
    path("logout", views.logout_view, name="logout"),

    # Main App Core
    path("home", views.home, name="home"),
    path("trending", views.trending, name="trending"),
    path("library", views.library, name="library"),
    path("favorites", views.favorites, name="favorites"),
    path("playlist", views.playlist, name="playlist"),
    path("playlist/<int:playlist_id>", views.playlist_detail, name="playlist_detail"),
    path("profile", views.profile, name="profile"),
    path("music_library", views.music_library, name="music_library"),
    path("video_library", views.video_library, name="video_library"),

    # Uploads & User Vault (20 free upload limit & YouTube importer)
    path("upload", views.upload_song, name="upload_song"),
    path("upload_url", views.upload_song, name="upload_url"),
    path("my_uploads", views.my_uploads, name="my_uploads"),
    path("my_uploads/delete/<int:song_id>", views.delete_user_song, name="delete_user_song"),

    # Premium Subscription System
    path("premium", views.upgrade_premium, name="upgrade_premium"),
    path("premium/activate", views.activate_premium, name="activate_premium"),
    path("premium/cancel", views.cancel_premium, name="cancel_premium"),

    # AJAX Endpoints
    path("toggle-favorite", views.toggle_favorite, name="toggle_favorite"),
    path("get-playlists", views.get_playlists, name="get_playlists"),
    path("add-to-playlist", views.add_to_playlist, name="add_to_playlist"),
    path("remove-from-playlist", views.remove_from_playlist, name="remove_from_playlist"),
    path("create-playlist", views.create_playlist, name="create_playlist"),
    path("record-play", views.record_play, name="record_play"),

    # Admin panel
    path("a/login", views.admin_login, name="admin_login"),
    path("a/logout", views.admin_logout, name="admin_logout"),
    path("a/dashboard", views.admin_dashboard, name="admin_dashboard"),
    path("a/users", views.admin_users, name="admin_users"),
    path("a/users/add", views.add_user, name="add_user"),
    path("a/users/edit/<int:user_id>", views.edit_user, name="edit_user"),
    path("a/users/delete/<int:user_id>", views.delete_user, name="delete_user"),
    path("a/users/toggle-premium/<int:user_id>", views.admin_toggle_premium, name="admin_toggle_premium"),
    path("a/songs", views.admin_songs, name="admin_songs"),
    path("a/songs/add", views.add_song, name="add_song"),
    path("a/songs/edit/<int:song_id>", views.edit_song, name="edit_song"),
    path("a/songs/delete/<int:song_id>", views.delete_song, name="delete_song"),
    path("a/songs/toggle-public/<int:song_id>", views.admin_toggle_song_public, name="admin_toggle_song_public"),
    path("a/songs/toggle-premium/<int:song_id>", views.admin_toggle_song_premium, name="admin_toggle_song_premium"),
    path("a/videos", views.admin_video, name="admin_video"),
]
