from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login
from django.contrib import messages
# Create your views here.

def index(request):
    return JsonResponse({"HELLO": "MESSAGE"})

def admin_dashboard(request):
    # Static values instead of database queries
    total_users = 150
    total_songs = 500
    total_playlists = 75

    # Static list of recent songs (dummy data)
    recent_songs = [
        {"title": "Blinding Lights", "artist": "The Weeknd", "cover": "songs/blinding_lights.jpg"},
        {"title": "Levitating", "artist": "Dua Lipa", "cover": "songs/levitating.jpg"},
        {"title": "Shape of You", "artist": "Ed Sheeran", "cover": "songs/shape_of_you.jpg"},
        {"title": "Peaches", "artist": "Justin Bieber", "cover": "songs/peaches.jpg"},
        {"title": "Save Your Tears", "artist": "The Weeknd", "cover": "songs/save_your_tears.jpg"},
        {"title": "Watermelon Sugar", "artist": "Harry Styles", "cover": "songs/watermelon_sugar.jpg"},
    ]

    # Static list of recent artists (dummy data)
    recent_artists = [
        {"name": "The Weeknd", "image": "artists/The-Weeknd.png"},
        {"name": "Dua Lipa", "image": "artists/dua-lipa.jpg"},
        {"name": "Ed Sheeran", "image": "artists/Ed-Sheeran.jpg"},
        {"name": "Ariana Grande", "image": "artists/ariana-grande.avif"},
        {"name": "Justin Bieber", "image": "artists/justin_bieber.jpg"},
        {"name": "Harry Styles", "image": "artists/harry_styles.jpg"},
    ]

    # Static list of most played songs (dummy data)
    most_played = [
        {"title": "Shape of You", "artist": "Ed Sheeran", "cover": "songs/shape_of_you.jpg", "play_count": 1200},
        {"title": "Blinding Lights", "artist": "The Weeknd", "cover": "songs/blinding_lights.jpg", "play_count": 1150},
        {"title": "Levitating", "artist": "Dua Lipa", "cover": "songs/levitating.jpg", "play_count": 980},
        {"title": "Peaches", "artist": "Justin Bieber", "cover": "songs/peaches.jpg", "play_count": 940},
        {"title": "Save Your Tears", "artist": "The Weeknd", "cover": "songs/save_your_tears.jpg", "play_count": 900},
        {"title": "Watermelon Sugar", "artist": "Harry Styles", "cover": "songs/watermelon_sugar.jpg", "play_count": 850},
    ]

    return render(request, 'admin/layout/admin_dashboard.html', {
        'total_users': total_users,
        'total_songs': total_songs,
        'total_playlists': total_playlists,
        'recent_songs': recent_songs,
        'recent_artists': recent_artists,
        'most_played': most_played,
    })

def admin_songs(request):
    # songs = Song.objects.all()
    songs = [
        {"title": "Blinding Lights", "artist": "The Weeknd", "cover": "songs/blinding_lights.jpg"},
        {"title": "Levitating", "artist": "Dua Lipa", "cover": "songs/levitating.jpg"},
        {"title": "Shape of You", "artist": "Ed Sheeran", "cover": "songs/shape_of_you.jpg"},
        {"title": "Peaches", "artist": "Justin Bieber", "cover": "songs/peaches.jpg"},
        {"title": "Save Your Tears", "artist": "The Weeknd", "cover": "songs/save_your_tears.jpg"},
        {"title": "Watermelon Sugar", "artist": "Harry Styles", "cover": "songs/watermelon_sugar.jpg"},
    ]
    return render(request, "admin/songs/admin_songs.html", {"songs": songs})

def delete_user(request):
    return render(request, "admin/users/admin_users.html")

def admin_video(request):
    return render(request, "admin/videos/admin_videos.html")
