from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm

def index(request):
    # Dummy Artist Data
    top_artists = [
        {"name": "The Weeknd", "image": "/static/images/The-Weeknd.png"},
        {"name": "Taylor Swift", "image": "/static/images/taylor-swift.png"},
        {"name": "Drake", "image": "/static/images/Drake.jpg"},
        {"name": "Ariana Grande", "image": "/static/images/ariana-grande.avif"},
        {"name": "Ed Sheeran", "image": "/static/images/Ed-Sheeran.jpg"},
        {"name": "BTS", "image": "/static/images/BTS.jpg"},
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
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")  # Change "home" to your actual home page URL name
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
    return render(request, "app/home.html")