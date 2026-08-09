import functools
import os
import re
import urllib.parse
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import FavoriteSong, Playlist, Song, User


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

def index(request):
    if request.user.is_authenticated:
        return redirect('home')
    trending_songs = Song.objects.filter(media_type='audio')[:4]
    top_artists = Song.objects.values('artist').annotate(song_count=Count('id')).order_by('-song_count')[:6]
    return render(request, "app/index.html", {
        "trending_songs": trending_songs,
        "top_artists": top_artists,
    })


def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            messages.error(request, "Invalid credentials")
        except User.DoesNotExist:
            messages.error(request, "User not found")

    return render(request, "app/auth/login.html")


def signup_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
        elif password1 != password2:
            messages.error(request, "Passwords do not match")
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            login(request, user)
            return redirect('home')

    return render(request, "app/auth/signup.html")


@login_required(login_url='login')
def home(request):
    trending_songs = Song.objects.filter(media_type='audio')[:3]
    latest_songs = Song.objects.filter(media_type='audio').order_by('-created_at')[:4]
    return render(request, "app/layout/home.html", {
        "trending_songs": trending_songs,
        "latest_songs": latest_songs,
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
    library_songs = Song.objects.all()
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


# ---------------------------------------------------------------------------
# AJAX endpoints
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@require_POST
def toggle_favorite(request):
    song_id = request.POST.get('song_id')
    try:
        song = Song.objects.get(id=song_id)
    except Song.DoesNotExist:
        return JsonResponse({'error': 'Song not found'}, status=404)

    fav, created = FavoriteSong.objects.get_or_create(user=request.user, song=song)
    if not created:
        fav.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})


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


# ---------------------------------------------------------------------------
# YouTube upload helpers
# ---------------------------------------------------------------------------

def extract_youtube_id(url):
    youtube_regex = re.compile(
        r'(https?://)?(www\.|m\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|shorts/|.+\?v=)?([^&=%\?]{11})'
    )
    match = youtube_regex.search(url or '')
    return match.group(6) if match else None


def get_youtube_info(youtube_id):
    """Fetch complete metadata for a YouTube video via yt-dlp.

    Returns a dict with keys: title, artist, album, thumbnail, duration,
    release_date -- or None on failure.
    """
    try:
        import yt_dlp
        opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={youtube_id}', download=False)
        if not info:
            return None

        # Duration (seconds -> timedelta)
        duration = None
        if info.get('duration'):
            duration = timedelta(seconds=int(info['duration']))

        # Release date (upload_date is YYYYMMDD -> YYYY-MM-DD)
        release_date = None
        upload_date = info.get('upload_date')
        if upload_date and len(str(upload_date)) == 8:
            release_date = f"{str(upload_date)[:4]}-{str(upload_date)[4:6]}-{str(upload_date)[6:8]}"

        return {
            'title': info.get('title'),
            'artist': info.get('artist') or info.get('uploader') or info.get('channel') or 'Unknown Artist',
            'album': info.get('album'),
            'thumbnail': info.get('thumbnail'),
            'duration': duration,
            'release_date': release_date,
        }
    except Exception:
        return None


def download_thumbnail(youtube_id, url):
    """Download the YouTube thumbnail and store it under MEDIA_ROOT/covers/.

    Returns a storage-relative path like 'covers/<youtube_id>.jpg' or None.
    """
    if not url:
        return None
    try:
        path = urllib.parse.urlparse(url).path
        ext = os.path.splitext(path)[1].lstrip('.').lower()
        if ext not in ('jpg', 'jpeg', 'png', 'webp'):
            ext = 'jpg'

        target_dir = os.path.join(settings.MEDIA_ROOT, 'covers')
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, f'{youtube_id}.{ext}')

        with urllib.request.urlopen(url, timeout=15) as response:
            data = response.read()
        if not data:
            return None
        with open(target_path, 'wb') as f:
            f.write(data)
        return f'covers/{youtube_id}.{ext}'
    except Exception:
        return None


def _find_downloaded_file(folder, youtube_id):
    """Locate the largest real media file downloaded for a youtube_id.

    Filters out yt-dlp sidecar files (.info.json, .part, etc.) and returns a
    storage-relative path, or None if nothing usable was found.
    """
    target_dir = os.path.join(settings.MEDIA_ROOT, folder)
    if not os.path.isdir(target_dir):
        return None
    skip = ('.info.json', '.description', '.part', '.tmp', '.jpg', '.webp', '.png')
    media = [
        f for f in os.listdir(target_dir)
        if f.startswith(youtube_id + '.') and not any(s in f for s in skip)
    ]
    if not media:
        return None
    media.sort(key=lambda f: os.path.getsize(os.path.join(target_dir, f)), reverse=True)
    return f'{folder}/{media[0]}'


def download_media(youtube_id, media_type):
    """Download the media file with yt-dlp into MEDIA_ROOT.

    Audio goes to MEDIA_ROOT/songs/ (converted to MP3 when FFmpeg is
    available, otherwise the best native audio format), video goes to
    MEDIA_ROOT/videos/ as MP4. Returns a storage-relative path or None.
    """
    try:
        import shutil

        import yt_dlp
        folder = 'songs' if media_type == 'audio' else 'videos'
        target_dir = os.path.join(settings.MEDIA_ROOT, folder)
        os.makedirs(target_dir, exist_ok=True)
        url = f'https://www.youtube.com/watch?v={youtube_id}'

        common = {
            'format': 'bestaudio/best' if media_type == 'audio' else 'best[ext=mp4]/best',
            'outtmpl': os.path.join(target_dir, f'{youtube_id}.%(ext)s'),
            'quiet': True,
            'noprogress': True,
            'no_warnings': True,
            'noplaylist': True,
        }

        if media_type == 'audio' and (shutil.which('ffmpeg') or shutil.which('avconv')):
            common['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        with yt_dlp.YoutubeDL(common) as ydl:
            ydl.extract_info(url, download=True)

        return _find_downloaded_file(folder, youtube_id)
    except Exception:
        return None


@login_required(login_url='login')
def upload_url(request):
    if request.method == "POST":
        content_url = request.POST.get('content_url')
        content_type = request.POST.get('content_type', 'music')
        store_locally = request.POST.get('store_locally') == 'on'

        youtube_id = extract_youtube_id(content_url)
        if not youtube_id:
            messages.error(request, "Invalid YouTube URL")
            return redirect('upload_url')

        if Song.objects.filter(youtube_id=youtube_id).exists():
            messages.warning(request, "This content is already in your library")
            return redirect('upload_url')

        media_type = 'audio' if content_type == 'music' else 'video'
        info = get_youtube_info(youtube_id)

        title = (info or {}).get('title') or f"YouTube {media_type.capitalize()} {youtube_id}"
        artist = (info or {}).get('artist') or "Unknown Artist"
        album = (info or {}).get('album') or None
        duration = (info or {}).get('duration')
        release_date = (info or {}).get('release_date') or "2024-01-01"

        song = Song.objects.create(
            title=title,
            artist=artist,
            album=album,
            genre="Other",
            release_date=release_date,
            duration=duration,
            youtube_id=youtube_id,
            media_type=media_type,
        )

        # Always try to store the thumbnail locally as the cover image
        cover_path = download_thumbnail(youtube_id, (info or {}).get('thumbnail'))
        if cover_path:
            song.cover_image = cover_path
            song.save()

        msg = f"Successfully added {media_type} from YouTube!"
        if store_locally:
            media_path = download_media(youtube_id, media_type)
            if media_path:
                song.audio_file = media_path
                song.save()
                msg += " Media file stored locally."
            else:
                msg += " Could not download the media file (metadata saved only)."
        messages.success(request, msg)
        return redirect('home')

    return render(request, "app/songs/upload_url.html")


# ---------------------------------------------------------------------------
# Admin helpers
# ---------------------------------------------------------------------------

def admin_required(view_func):
    @login_required(login_url='admin_login')
    @functools.wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "You need admin access to view this page.")
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped


def admin_login(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_dashboard')

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_obj = User.objects.filter(email=email).first()
        user = authenticate(request, username=user_obj.username, password=password) if user_obj else None
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect('admin_dashboard')
        messages.error(request, "Invalid admin credentials")

    return render(request, "admin/auth/admin_login.html")


@admin_required
def admin_logout(request):
    logout(request)
    return redirect('admin_login')


@admin_required
def admin_dashboard(request):
    recent_songs = Song.objects.order_by('-created_at')[:3]

    top_artists = Song.objects.values('artist').annotate(
        song_count=Count('id')).order_by('-song_count')[:4]
    recent_artists = []
    for item in top_artists:
        song = Song.objects.filter(artist=item['artist']).order_by('-created_at').first()
        recent_artists.append({
            'name': item['artist'],
            'image': song.cover_image.url if song and song.cover_image else f"{settings.STATIC_URL}artists/default.jpg",
        })

    most_played = Song.objects.annotate(
        favorite_count=Count('favorited_by')).order_by('-favorite_count')[:3]

    context = {
        "total_users": User.objects.count(),
        "total_songs": Song.objects.count(),
        "total_playlists": Playlist.objects.count(),
        "recent_songs": recent_songs,
        "recent_artists": recent_artists,
        "most_played": most_played,
    }
    return render(request, "admin/layout/admin_dashboard.html", context)


@admin_required
def admin_users(request):
    search = request.GET.get('search', '')
    users = User.objects.order_by('-date_joined')
    if search:
        users = users.filter(Q(username__icontains=search) | Q(email__icontains=search))
    page_obj = Paginator(users, 10).get_page(request.GET.get('page'))
    return render(request, "admin/users/admin_users.html", {
        "users": page_obj,
        "search_query": search,
    })


@admin_required
def add_user(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        elif email and User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
        elif not password:
            messages.error(request, "Password is required")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            if 'user_img' in request.FILES:
                user.profile_pic = request.FILES['user_img']
                user.save()
            messages.success(request, f"User '{username}' created successfully")
            return redirect('admin_users')

    return render(request, "admin/users/user_add.html")


@admin_required
def edit_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        if 'profile_picture' in request.FILES:
            user.profile_pic = request.FILES['profile_picture']
        user.save()
        messages.success(request, "User updated successfully")
        return redirect('admin_users')

    return render(request, "admin/users/user_edit.html", {"user": user})


@admin_required
@require_POST
def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user == request.user:
        messages.error(request, "You cannot delete your own account")
    else:
        username = user.username
        user.delete()
        messages.success(request, f"User '{username}' deleted successfully")
    return redirect('admin_users')


def parse_duration(value):
    if not value:
        return None
    try:
        parts = [int(p) for p in str(value).split(':')]
        if len(parts) == 3:
            hours, minutes, seconds = parts
        elif len(parts) == 2:
            hours, minutes, seconds = 0, parts[0], parts[1]
        elif len(parts) == 1:
            hours, minutes, seconds = 0, 0, parts[0]
        else:
            return None
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    except (ValueError, TypeError):
        return None


@admin_required
def admin_songs(request):
    search = request.GET.get('search', '')
    songs = Song.objects.order_by('-created_at')
    if search:
        songs = songs.filter(Q(title__icontains=search) | Q(artist__icontains=search))
    return render(request, "admin/songs/admin_songs.html", {
        "songs": songs,
        "search_query": search,
    })


@admin_required
def add_song(request):
    if request.method == "POST":
        title = request.POST.get('title')
        artist = request.POST.get('artist')
        genre = request.POST.get('genre', 'Other')
        release_date = request.POST.get('release_date')
        media_type = request.POST.get('media_type', 'audio')
        youtube_url = request.POST.get('youtube_url', '')
        youtube_id = extract_youtube_id(youtube_url) if youtube_url else None

        if youtube_id and Song.objects.filter(youtube_id=youtube_id).exists():
            messages.error(request, "A song with this YouTube URL already exists")
            return redirect('add_song')

        # Auto-fill details from YouTube when a valid URL was provided
        info = get_youtube_info(youtube_id) if youtube_id else None
        title = (info or {}).get('title') or title
        artist = (info or {}).get('artist') or artist
        if not release_date:
            release_date = (info or {}).get('release_date') or "2024-01-01"

        song = Song.objects.create(
            title=title,
            artist=artist,
            genre=genre,
            release_date=release_date,
            album=(info or {}).get('album'),
            duration=(info or {}).get('duration') or parse_duration(request.POST.get('duration')),
            media_type=media_type,
            youtube_id=youtube_id,
        )
        if 'audio_file' in request.FILES:
            song.audio_file = request.FILES['audio_file']
            song.save()

        # Store the YouTube thumbnail locally as the cover image
        if youtube_id:
            cover_path = download_thumbnail(youtube_id, (info or {}).get('thumbnail'))
            if cover_path:
                song.cover_image = cover_path
                song.save()

        messages.success(request, f"Song '{title}' added successfully")
        return redirect('admin_songs')

    return render(request, "admin/songs/add_song.html")


@admin_required
def edit_song(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    if request.method == "POST":
        song.title = request.POST.get('title', song.title)
        song.artist = request.POST.get('artist', song.artist)
        if 'audio_file' in request.FILES:
            song.audio_file = request.FILES['audio_file']
        song.save()
        messages.success(request, "Song updated successfully")
        return redirect('admin_songs')

    return render(request, "admin/songs/edit_song.html", {"song": song})


@admin_required
@require_POST
def delete_song(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    title = song.title
    song.delete()
    messages.success(request, f"Song '{title}' deleted successfully")
    return redirect('admin_songs')


@admin_required
def admin_video(request):
    search = request.GET.get('search', '')
    videos = Song.objects.filter(media_type='video').order_by('-created_at')
    if search:
        videos = videos.filter(Q(title__icontains=search) | Q(artist__icontains=search))
    page_obj = Paginator(videos, 10).get_page(request.GET.get('page'))
    return render(request, "admin/videos/admin_videos.html", {
        "videos": page_obj,
        "search_query": search,
    })
