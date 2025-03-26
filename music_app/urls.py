from django.urls import path
from music_app.view import authentication

urlpatterns = [
    path("", authentication.index, name="index"),
    path("login", authentication.login_view, name="login"),
    path("signup", authentication.signup_view, name="signup"),
    path("home", authentication.home, name="home"),
    path("upload_url", authentication.upload_url, name="upload_url"),
]