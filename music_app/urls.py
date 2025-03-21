from django.urls import path
from music_app.view import authentication

urlpatterns = [
    path("login", authentication.login_view, name="login"),
    path("signup", authentication.signup_view, name="signup"),
    path("home", authentication.home, name="home"),
]