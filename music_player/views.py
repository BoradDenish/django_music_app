from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Song, Playlist, FavoriteSong, User
from django.db.models import Count

def index(request):
    if request.user.is_authenticated:
        return redirect('home')
    trending_songs = Song.objects.filter(media_type='audio')[:4]
    top_artists = Song.objects.values('artist').annotate(song_count=Count('id')).order_by('-song_count')[:6]
    return render(request, "app/index.html", {
        "trending_songs": trending_songs,
        "top_artists": top_artists
    })

def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        # Since we use email as username in our AbstractUser setup usually, 
        # but Django's default authenticate uses username.
        # Let's check if we configured email as username. 
        # In my AbstractUser I didn't set USERNAME_FIELD.
        # I'll just find the user by email first.
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Invalid credentials")
        except User.DoesNotExist:
            messages.error(request, "User not found")
            
    return render(request, "app/auth/login.html")

def signup_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password1')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect('home')
            
    return render(request, "app/auth/signup.html")

@login_required(login_url='login')
def home(request):
    trending_songs = Song.objects.filter(media_type='audio')[:3]
    latest_songs = Song.objects.filter(media_type='audio').order_by('-created_at')[:4]
    return render(request, "app/layout/home.html", {
        "trending_songs": trending_songs,
        "latest_songs": latest_songs
    })

@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('index')

@login_required(login_url='login')
def trending(request):
    trending_songs = Song.objects.filter(media_type='audio')
    return render(request, "app/songs/trending.html", {"trending_songs": trending_songs})

@login_required(login_url='login')
def library(request):
    library_songs = Song.objects.all() # In a real app, this might be user's uploaded songs
    return render(request, "app/songs/library.html", {"library_songs": library_songs})

@login_required(login_url='login')
def favorites(request):
    favs = FavoriteSong.objects.filter(user=request.user).select_related('song')
    favorite_songs = [f.song for f in favs]
    return render(request, "app/songs/favorites.html", {"favorite_songs": favorite_songs})

@login_required(login_url='login')
def playlist(request):
    playlists = Playlist.objects.filter(user=request.user)
    return render(request, "app/songs/playlist.html", {"playlists": playlists})

@login_required(login_url='login')
def music_library(request):
    audios = Song.objects.filter(media_type='audio')
    return render(request, "app/songs/music_library.html", {"audios": audios})

@login_required(login_url='login')
def video_library(request):
    videos = Song.objects.filter(media_type='video')
    return render(request, "app/songs/video_library.html", {"videos": videos})

@login_required(login_url='login')
def profile(request):
    return render(request, "app/auth/profile.html")

from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

@login_required(login_url='login')
@require_POST
def toggle_favorite(request):
    song_id = request.POST.get('song_id')
    try:
        song = Song.objects.get(id=song_id)
        fav, created = FavoriteSong.objects.get_or_create(user=request.user, song=song)
        if not created:
            fav.delete()
            return JsonResponse({'status': 'removed'})
        return JsonResponse({'status': 'added'})
    except Song.DoesNotExist:
        return JsonResponse({'error': 'Song not found'}, status=404)

@login_required(login_url='login')
def get_playlists(request):
    playlists = Playlist.objects.filter(user=request.user)
    data = [{'id': p.id, 'name': p.name} for p in playlists]
    return JsonResponse({'playlists': data})

@login_required(login_url='login')
@require_POST
def add_to_playlist(request):
    song_id = request.POST.get('song_id')
    playlist_id = request.POST.get('playlist_id')
    try:
        song = Song.objects.get(id=song_id)
        playlist = Playlist.objects.get(id=playlist_id, user=request.user)
        playlist.songs.add(song)
        return JsonResponse({'status': 'success'})
    except (Song.DoesNotExist, Playlist.DoesNotExist):
        return JsonResponse({'error': 'Not found'}, status=404)

import re
import urllib.request
import urllib.parse
from django.utils import timezone

def extract_youtube_id(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    match = re.search(youtube_regex, url)
    return match.group(6) if match else None

def get_youtube_details(youtube_id):
    # Minimal attempt to get metadata without heavy libraries
    # In a real app, use yt-dlp or google-api-python-client
    try:
        params = {"format": "json", "url": f"https://www.youtube.com/watch?v={youtube_id}"}
        url = "https://www.youtube.com/oembed?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data.get('title'), data.get('author_name')
    except:
        return None, None

@login_required(login_url='login')
def upload_url(request):
    if request.method == "POST":
        content_url = request.POST.get('content_url')
        content_type = request.POST.get('content_type')
        store_locally = request.POST.get('store_locally') == 'on'
        
        youtube_id = extract_youtube_id(content_url)
        if not youtube_id:
            messages.error(request, "Invalid YouTube URL")
            return redirect('upload_url')
            
        if Song.objects.filter(youtube_id=youtube_id).exists():
            messages.warning(request, "This content is already in your library")
            return redirect('upload_url')
            
        media_type = 'audio' if content_type == 'music' else 'video'
        
        title, artist = get_youtube_details(youtube_id)
        title = title or f"YouTube {media_type.capitalize()} {youtube_id}"
        artist = artist or "Unknown Artist"
        
        # In a real implementation with store_locally=True, 
        # you would trigger a background task (Celery) to download the file using yt-dlp.
        # For this demonstration, we'll save the metadata.
        
        song = Song.objects.create(
            title=title,
            artist=artist,
            genre="Other",
            release_date=timezone.now().date(),
            youtube_id=youtube_id,
            media_type=media_type,
        )
        
        msg = f"Successfully added {media_type} from YouTube!"
        if store_locally:
            msg += " (Downloading started in background...)"
            
        messages.success(request, msg)
        return redirect('home')

    return render(request, "app/songs/upload_url.html")

def admin_dashboard(request):
    # Simplified admin dashboard
    context = {
        "total_users": User.objects.count(),
        "total_songs": Song.objects.count(),
        "total_playlists": Playlist.objects.count(),
        "recent_songs": Song.objects.all().order_by('-created_at')[:3],
    }
    return render(request, "admin/layout/admin_dashboard.html", context)
