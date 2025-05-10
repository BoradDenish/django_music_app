from django.urls import path
from music_app.view import authentication

urlpatterns = [
    path("", authentication.index, name="index"),
    path("login", authentication.login_view, name="login"),
    path("signup", authentication.signup_view, name="signup"),
    path("home", authentication.home, name="home"),
    path("upload_url", authentication.upload_url, name="upload_url"),
    path("trending", authentication.trending, name="trending"),
    path("library", authentication.library, name="library"),
    path("logout", authentication.logout_view, name="logout"),
    path("favorites", authentication.favorites, name="favorites"),
    path("playlist", authentication.playlist, name="playlist"),
    path("profile", authentication.profile, name="profile"),
]