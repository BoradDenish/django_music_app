from datetime import datetime, timedelta
import secrets
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from django.contrib.auth.hashers import check_password

from music_admin.models import Session, User

def index(request):
    # Dummy Artist Data
    top_artists = [
        {"name": "The Weeknd", "image": "/static/artists/The-Weeknd.png"},
        {"name": "Taylor Swift", "image": "/static/artists/taylor-swift.png"},
        {"name": "Drake", "image": "/static/artists/Drake.jpg"},
        {"name": "Ariana Grande", "image": "/static/artists/ariana-grande.avif"},
        {"name": "Ed Sheeran", "image": "/static/artists/Ed-Sheeran.jpg"},
        {"name": "BTS", "image": "/static/artists/BTS.jpg"},
    ]

    # Dummy Song Data
    trending_songs = [
        {"title": "Blinding Lights", "artist": "The Weeknd", "cover": "/static/images/song1.jpg"},
        {"title": "Shake It Off", "artist": "Taylor Swift", "cover": "/static/images/song2.jpg"},
        {"title": "God's Plan", "artist": "Drake", "cover": "/static/images/song3.jpg"},
        {"title": "7 Rings", "artist": "Ariana Grande", "cover": "/static/images/song4.jpg"},
        {"title": "Shape of You", "artist": "Ed Sheeran", "cover": "/static/images/song5.jpg"},
        {"title": "Dynamite", "artist": "BTS", "cover": "/static/images/song6.jpg"},
    ]

    return render(request, "app/index.html", {"top_artists": top_artists, "trending_songs": trending_songs})


def login_view(request):
    if request.method == "POST":
        useremail = request.POST.get("email")
        password  = request.POST.get("password")
        if not useremail or not password:
            return render(request, "app/auth/login.html", {"error": "Please enter both useremail and password."})
        
        # Fetch user record safely
        user = User.objects.exclude(user_status=0).exclude(user_role=1).filter(user_email=useremail).first()

        if not user:
            return JsonResponse({"status": 500, "message": "Email does not exist!"})

        # Validate password
        if not check_password(password, user.user_password):
            return JsonResponse({"status": 500, "message": "Invalid password! Please try again."})

        # Generate session token
        session_token = secrets.token_hex()

        # Store session token securely
        request.session["user_session"] = {
            "session_token": session_token,
            "session_name": "user_session",
        }
        request.session["user_profile"] = user.user_profile_pic.url if user.user_profile_pic else None

        # Set session expiry
        exp_time = timezone.now() + timedelta(days=1)

        # Store session in the database
        session_data = Session(
            session_user=user,
            session_email=useremail,
            session_token=session_token,
            session_expire=exp_time,
            session_status=1,
            created_at=datetime.now(),
        )
        session_data.save()
        
        # user = authenticate(request, username=username, password=password)
        if user is not None:
            # login(request, user)
            return redirect("home")
    return render(request, "app/auth/login.html")


def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "app/auth/signup.html", {"form": form})

def home(request):
    return render(request, "app/layout/home.html")

def upload_url(request):
    return render(request, "app/songs/upload_url.html")

def trending(request):
    return render(request, "app/songs/trending.html")

def library(request):
    return render(request, "app/songs/library.html")

def logout_view(request):
    # Clear session data
    if "user_session" in request.session:
        del request.session["user_session"]
    if "user_profile" in request.session:
        del request.session["user_profile"]

    # Redirect to login page
    return redirect("login")

def favorites(request):
    return render(request, "app/songs/favorites.html")

def playlist(request):
    return render(request, "app/songs/playlist.html")

def profile(request):
    # Dummy User Data
    user_data = {
        "name": "John Doe",
        "email": "john@gmail.com",
    }
    return render(request, "app/auth/profile.html", {"user_data": user_data})