from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("signup", views.signup_view, name="signup"),
    path("home", views.home, name="home"),
    path("logout", views.logout_view, name="logout"),
    path("trending", views.trending, name="trending"),
    # Add other paths as needed
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
    
    # Admin dashboard (simplified)
    path("admin-dashboard", views.admin_dashboard, name="admin_dashboard"),
]
