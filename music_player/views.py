import functools
import os
import re
import shutil
import urllib.parse
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import FavoriteSong, Playlist, Song, User


# ---------------------------------------------------------------------------
# Query Helpers
# ---------------------------------------------------------------------------

def get_user_songs_queryset(user, media_type=None):
    """
    Returns songs accessible to the given user:
    - Public songs (admin/system created or is_public=True)
    - Private songs uploaded specifically by this user
    Other users' private songs are strictly excluded.
    """
    if user.is_authenticated:
        qs = Song.objects.filter(Q(is_public=True) | Q(uploaded_by=user))
    else:
        qs = Song.objects.filter(is_public=True)

    if media_type:
        qs = qs.filter(media_type=media_type)
    return qs


# ---------------------------------------------------------------------------
# Public pages & Authentication
# ---------------------------------------------------------------------------

def index(request):
    if request.user.is_authenticated:
        return redirect('home')
    trending_songs = Song.objects.filter(is_public=True, media_type='audio').order_by('-play_count', '-created_at')[:8]
    top_artists = Song.objects.filter(is_public=True).values('artist').annotate(song_count=Count('id')).order_by('-song_count')[:6]
    return render(request, "app/index.html", {
        "trending_songs": trending_songs,
        "top_artists": top_artists,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        login_input = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user = None
        # Allow login via username or email
        if '@' in login_input:
            user_obj = User.objects.filter(email__iexact=login_input).first()
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)
        else:
            user = authenticate(request, username=login_input, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home')
        messages.error(request, "Invalid username/email or password.")

    return render(request, "app/auth/login.html")


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Username is already taken.")
        elif email and User.objects.filter(email__iexact=email).exists():
            messages.error(request, "An account with this email already exists.")
        elif password1 != password2:
            messages.error(request, "Passwords do not match.")
        elif len(password1) < 6:
            messages.error(request, "Password must be at least 6 characters.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            if phone:
                user.user_phone = phone
                user.save()
            login(request, user)
            messages.success(request, f"Account created! Welcome to MusicApp, {username}!")
            return redirect('home')

    return render(request, "app/auth/signup.html")


@login_required(login_url='login')
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('index')


# ---------------------------------------------------------------------------
# User Core App Views
# ---------------------------------------------------------------------------

@login_required(login_url='login')
def home(request):
    accessible_songs = get_user_songs_queryset(request.user, media_type='audio')
    trending_songs = accessible_songs.order_by('-play_count', '-created_at')[:6]
    latest_songs = accessible_songs.order_by('-created_at')[:10]
    user_uploads = Song.objects.filter(uploaded_by=request.user).order_by('-created_at')[:4]
    premium_songs = accessible_songs.filter(is_premium=True).order_by('-created_at')[:4]

    return render(request, "app/layout/home.html", {
        "trending_songs": trending_songs,
        "latest_songs": latest_songs,
        "user_uploads": user_uploads,
        "premium_songs": premium_songs,
    })


@login_required(login_url='login')
def trending(request):
    trending_songs = get_user_songs_queryset(request.user, media_type='audio').order_by('-play_count', '-created_at')
    return render(request, "app/songs/trending.html", {"trending_songs": trending_songs})


@login_required(login_url='login')
def library(request):
    accessible_songs = get_user_songs_queryset(request.user)
    playlists = Playlist.objects.filter(user=request.user)
    fav_count = FavoriteSong.objects.filter(user=request.user).count()
    uploaded_count = Song.objects.filter(uploaded_by=request.user).count()

    search = request.GET.get('search', '').strip()
    if search:
        accessible_songs = accessible_songs.filter(
            Q(title__icontains=search) | Q(artist__icontains=search) | Q(album__icontains=search) | Q(genre__icontains=search)
        )

    return render(request, "app/songs/library.html", {
        "library_songs": accessible_songs,
        "playlists": playlists,
        "fav_count": fav_count,
        "uploaded_count": uploaded_count,
        "search_query": search,
    })


@login_required(login_url='login')
def favorites(request):
    favs = FavoriteSong.objects.filter(user=request.user).select_related('song').order_by('-created_at')
    favorite_songs = [f.song for f in favs]
    return render(request, "app/songs/favorites.html", {"favorite_songs": favorite_songs})


@login_required(login_url='login')
def playlist(request):
    playlists = Playlist.objects.filter(user=request.user).annotate(song_count=Count('songs')).order_by('-updated_at')

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            Playlist.objects.create(user=request.user, name=name, description=description)
            messages.success(request, f"Playlist '{name}' created successfully!")
            return redirect('playlist')

    return render(request, "app/songs/playlist.html", {"playlists": playlists})


@login_required(login_url='login')
def playlist_detail(request, playlist_id):
    playlist_obj = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    return render(request, "app/songs/playlist_detail.html", {
        "playlist": playlist_obj,
        "songs": playlist_obj.songs.all()
    })


@login_required(login_url='login')
def music_library(request):
    genre_filter = request.GET.get('genre', '')
    search = request.GET.get('search', '').strip()

    audios = get_user_songs_queryset(request.user, media_type='audio').order_by('-created_at')
    if genre_filter:
        audios = audios.filter(genre__iexact=genre_filter)
    if search:
        audios = audios.filter(Q(title__icontains=search) | Q(artist__icontains=search) | Q(album__icontains=search))

    genres = [g[0] for g in Song.GENRE_CHOICES]
    return render(request, "app/songs/music_library.html", {
        "audios": audios,
        "genres": genres,
        "selected_genre": genre_filter,
        "search_query": search,
    })


@login_required(login_url='login')
def video_library(request):
    search = request.GET.get('search', '').strip()
    videos = get_user_songs_queryset(request.user, media_type='video').order_by('-created_at')
    if search:
        videos = videos.filter(Q(title__icontains=search) | Q(artist__icontains=search))

    return render(request, "app/songs/video_library.html", {
        "videos": videos,
        "search_query": search,
    })


@login_required(login_url='login')
def profile(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        if email:
            request.user.email = email
        if phone:
            request.user.user_phone = phone
        if 'profile_pic' in request.FILES:
            request.user.profile_pic = request.FILES['profile_pic']
        request.user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

    user_songs_count = Song.objects.filter(uploaded_by=request.user).count()
    return render(request, "app/auth/profile.html", {
        "user_songs_count": user_songs_count,
    })


# ---------------------------------------------------------------------------
# My Uploads & Quota System (20 songs for free users, unlimited for premium)
# ---------------------------------------------------------------------------

@login_required(login_url='login')
def my_uploads(request):
    user_songs = Song.objects.filter(uploaded_by=request.user).order_by('-created_at')
    return render(request, "app/songs/my_uploads.html", {
        "user_songs": user_songs,
        "can_upload": request.user.can_upload(),
        "uploaded_count": request.user.uploaded_count,
        "upload_limit": request.user.upload_limit,
        "uploads_remaining": request.user.uploads_remaining,
        "upload_percentage": request.user.upload_percentage,
    })


@login_required(login_url='login')
@require_POST
def delete_user_song(request, song_id):
    song = get_object_or_404(Song, pk=song_id, uploaded_by=request.user)
    title = song.title

    # Remove media files if local
    if song.audio_file and os.path.exists(song.audio_file.path):
        try:
            os.remove(song.audio_file.path)
        except Exception:
            pass

    song.delete()
    messages.success(request, f"Deleted '{title}' from your uploads. Upload slot freed up!")
    return redirect('my_uploads')


# ---------------------------------------------------------------------------
# Premium Membership System
# ---------------------------------------------------------------------------

@login_required(login_url='login')
def upgrade_premium(request):
    return render(request, "app/auth/premium.html", {
        "uploaded_count": request.user.uploaded_count,
        "upload_limit": request.user.upload_limit,
        "uploads_remaining": request.user.uploads_remaining,
    })


@login_required(login_url='login')
@require_POST
def activate_premium(request):
    plan = request.POST.get('plan', 'monthly')
    duration_days = 365 if plan == 'annual' else 30

    request.user.is_premium = True
    request.user.premium_expiry = timezone.now() + timedelta(days=duration_days)
    request.user.save()

    messages.success(
        request,
        f"🎉 Congratulations! You are now a VIP Premium Member ({plan.capitalize()} Plan). "
        f"You have unlocked Unlimited Song Uploads and High-Fidelity Audio!"
    )
    return redirect('profile')


@login_required(login_url='login')
@require_POST
def cancel_premium(request):
    request.user.is_premium = False
    request.user.premium_expiry = None
    request.user.save()
    messages.info(request, "Your Premium VIP subscription has been deactivated.")
    return redirect('profile')


# ---------------------------------------------------------------------------
# YouTube & Direct Media Processing
# ---------------------------------------------------------------------------

def extract_youtube_id(url):
    youtube_regex = re.compile(
        r'(https?://)?(www\.|m\.|music\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|shorts/|.+\?v=)?([^&=%\?]{11})'
    )
    match = youtube_regex.search(url or '')
    return match.group(6) if match else None


def get_youtube_info(youtube_id):
    """Fetch complete metadata for a YouTube video via yt-dlp."""
    try:
        import yt_dlp
        opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'skip_download': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'socket_timeout': 10,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={youtube_id}', download=False)
        if not info:
            return None

        # Duration
        duration = None
        if info.get('duration'):
            duration = timedelta(seconds=int(info['duration']))

        # Release date
        release_date = None
        upload_date = info.get('upload_date')
        if upload_date and len(str(upload_date)) == 8:
            release_date = f"{str(upload_date)[:4]}-{str(upload_date)[4:6]}-{str(upload_date)[6:8]}"

        # Best thumbnail
        thumbnails = info.get('thumbnails') or []
        best_thumb = info.get('thumbnail')
        if thumbnails:
            valid_thumbs = [t for t in thumbnails if t.get('url')]
            if valid_thumbs:
                valid_thumbs.sort(key=lambda x: (x.get('preference', 0), x.get('width', 0) or 0), reverse=True)
                best_thumb = valid_thumbs[0].get('url')

        return {
            'title': info.get('title'),
            'artist': info.get('artist') or info.get('uploader') or info.get('channel') or 'YouTube Artist',
            'album': info.get('album'),
            'thumbnail': best_thumb,
            'duration': duration,
            'release_date': release_date,
        }
    except Exception as e:
        print(f"Error fetching YouTube info for {youtube_id}: {e}")
        return None


def download_thumbnail(youtube_id, url):
    """Download thumbnail and store under MEDIA_ROOT/covers/."""
    target_dir = os.path.join(settings.MEDIA_ROOT, 'covers')
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, f'{youtube_id}.jpg')

    urls_to_try = [url, f"https://img.youtube.com/vi/{youtube_id}/maxresdefault.jpg", f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg"]
    for u in urls_to_try:
        if not u:
            continue
        try:
            req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read()
            if data and len(data) > 1000:
                with open(target_path, 'wb') as f:
                    f.write(data)
                return f'covers/{youtube_id}.jpg'
        except Exception:
            continue
    return None


def _find_downloaded_file(folder, youtube_id):
    """Locate the downloaded media file for youtube_id."""
    target_dir = os.path.join(settings.MEDIA_ROOT, folder)
    if not os.path.isdir(target_dir):
        return None
    skip = ('.info.json', '.description', '.part', '.tmp', '.jpg', '.webp', '.png', '.ytdl')
    media = [
        f for f in os.listdir(target_dir)
        if f.startswith(youtube_id + '.') and not any(s in f for s in skip)
    ]
    if not media:
        return None
    media.sort(key=lambda f: os.path.getsize(os.path.join(target_dir, f)), reverse=True)
    return f'{folder}/{media[0]}'


def download_media(youtube_id, media_type='audio'):
    """Download audio/video stream using yt-dlp to MEDIA_ROOT."""
    try:
        import yt_dlp
        folder = 'songs' if media_type == 'audio' else 'videos'
        target_dir = os.path.join(settings.MEDIA_ROOT, folder)
        os.makedirs(target_dir, exist_ok=True)
        url = f'https://www.youtube.com/watch?v={youtube_id}'

        common = {
            'outtmpl': os.path.join(target_dir, f'{youtube_id}.%(ext)s'),
            'quiet': True,
            'noprogress': True,
            'no_warnings': True,
            'noplaylist': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'socket_timeout': 15,
        }

        has_ffmpeg = shutil.which('ffmpeg') or shutil.which('avconv')
        if media_type == 'audio':
            if has_ffmpeg:
                common['format'] = 'bestaudio/best'
                common['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                common['format'] = 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best'
        else:
            common['format'] = 'best[ext=mp4]/best'

        with yt_dlp.YoutubeDL(common) as ydl:
            ydl.extract_info(url, download=True)

        return _find_downloaded_file(folder, youtube_id)
    except Exception as e:
        print(f"Error downloading media for {youtube_id}: {e}")
        return None


def parse_duration_str(value):
    if not value:
        return None
    try:
        parts = [int(p) for p in str(value).split(':')]
        if len(parts) == 3:
            return timedelta(hours=parts[0], minutes=parts[1], seconds=parts[2])
        elif len(parts) == 2:
            return timedelta(minutes=parts[0], seconds=parts[1])
        elif len(parts) == 1:
            return timedelta(seconds=parts[0])
    except (ValueError, TypeError):
        pass
    return None


@login_required(login_url='login')
def upload_song(request):
    """
    Unified Upload View: Supports YouTube URL Import AND Direct File Upload.
    Enforces user quota (20 songs for free users, unlimited for premium/admin).
    Admin uploads are public by default; regular user uploads are private to the user.
    """
    # 1. Check upload limit
    if not request.user.can_upload():
        messages.error(
            request,
            f"⚠️ Upload limit reached ({request.user.uploaded_count}/20 songs). "
            f"Please upgrade to Premium VIP to unlock unlimited song uploads!"
        )
        return redirect('upgrade_premium')

    if request.method == "POST":
        upload_type = request.POST.get('upload_type', 'youtube')  # 'youtube' or 'file'

        if upload_type == 'youtube':
            content_url = request.POST.get('content_url', '').strip()
            media_type = request.POST.get('content_type', 'audio')
            store_locally = request.POST.get('store_locally') in ('on', 'true', '1')

            youtube_id = extract_youtube_id(content_url)
            if not youtube_id:
                messages.error(request, "Invalid YouTube URL. Please enter a valid YouTube or YouTube Music link.")
                return redirect('upload_url')

            # Fetch metadata
            info = get_youtube_info(youtube_id)
            title = (info or {}).get('title') or f"YouTube {media_type.capitalize()} Track"
            artist = (info or {}).get('artist') or "YouTube Artist"
            album = (info or {}).get('album')
            duration = (info or {}).get('duration')
            release_date = (info or {}).get('release_date') or timezone.now().date()

            # Create song
            is_admin = request.user.is_staff or request.user.is_superuser
            song = Song.objects.create(
                title=title,
                artist=artist,
                album=album,
                genre="Other",
                release_date=release_date,
                duration=duration,
                youtube_id=youtube_id,
                media_type=media_type,
                uploaded_by=request.user,
                is_public=is_admin,  # Admin uploads are public, user uploads private
                is_premium=False,
            )

            # Download poster
            cover_path = download_thumbnail(youtube_id, (info or {}).get('thumbnail'))
            if cover_path:
                song.cover_image.name = cover_path
                song.save()

            # Download audio/video stream
            if store_locally:
                media_path = download_media(youtube_id, media_type)
                if media_path:
                    song.audio_file.name = media_path
                    song.save()

            messages.success(request, f"🎉 Successfully imported '{title}' into your library!")
            return redirect('my_uploads' if not is_admin else 'home')

        else:
            # Direct file upload
            title = request.POST.get('title', '').strip()
            artist = request.POST.get('artist', '').strip() or "Unknown Artist"
            album = request.POST.get('album', '').strip()
            genre = request.POST.get('genre', 'Other')
            release_date = request.POST.get('release_date') or timezone.now().date()
            duration_str = request.POST.get('duration', '')
            media_type = request.POST.get('media_type', 'audio')

            if not title:
                messages.error(request, "Song title is required.")
                return redirect('upload_url')

            if 'audio_file' not in request.FILES:
                messages.error(request, "Please select an audio file to upload.")
                return redirect('upload_url')

            is_admin = request.user.is_staff or request.user.is_superuser
            song = Song.objects.create(
                title=title,
                artist=artist,
                album=album,
                genre=genre,
                release_date=release_date,
                duration=parse_duration_str(duration_str),
                media_type=media_type,
                uploaded_by=request.user,
                is_public=is_admin,
                is_premium=False,
            )

            song.audio_file = request.FILES['audio_file']
            if 'cover_image' in request.FILES:
                song.cover_image = request.FILES['cover_image']
            song.save()

            messages.success(request, f"🎉 Song '{title}' uploaded successfully to your collection!")
            return redirect('my_uploads' if not is_admin else 'home')

    return render(request, "app/songs/upload_url.html", {
        "can_upload": request.user.can_upload(),
        "uploaded_count": request.user.uploaded_count,
        "upload_limit": request.user.upload_limit,
        "uploads_remaining": request.user.uploads_remaining,
        "genres": [g[0] for g in Song.GENRE_CHOICES],
    })


# Legacy alias
upload_url = upload_song


# ---------------------------------------------------------------------------
# AJAX Endpoints
# ---------------------------------------------------------------------------

@login_required(login_url='login')
@require_POST
def toggle_favorite(request):
    song_id = request.POST.get('song_id')
    song = get_object_or_404(Song, id=song_id)

    fav, created = FavoriteSong.objects.get_or_create(user=request.user, song=song)
    if not created:
        fav.delete()
        return JsonResponse({'status': 'removed', 'count': FavoriteSong.objects.filter(user=request.user).count()})
    return JsonResponse({'status': 'added', 'count': FavoriteSong.objects.filter(user=request.user).count()})


@login_required(login_url='login')
def get_playlists(request):
    playlists = Playlist.objects.filter(user=request.user).values('id', 'name')
    return JsonResponse({'playlists': list(playlists)})


@login_required(login_url='login')
@require_POST
def add_to_playlist(request):
    song_id = request.POST.get('song_id')
    playlist_id = request.POST.get('playlist_id')

    song = get_object_or_404(Song, id=song_id)
    playlist_obj = get_object_or_404(Playlist, id=playlist_id, user=request.user)

    if playlist_obj.songs.filter(id=song.id).exists():
        return JsonResponse({'status': 'already_in', 'message': f"'{song.title}' is already in this playlist."})

    playlist_obj.songs.add(song)
    playlist_obj.save()
    return JsonResponse({'status': 'success', 'message': f"Added '{song.title}' to playlist '{playlist_obj.name}'!"})


@login_required(login_url='login')
@require_POST
def remove_from_playlist(request):
    song_id = request.POST.get('song_id')
    playlist_id = request.POST.get('playlist_id')

    playlist_obj = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    song = get_object_or_404(Song, id=song_id)
    playlist_obj.songs.remove(song)
    return JsonResponse({'status': 'success'})


@login_required(login_url='login')
@require_POST
def create_playlist(request):
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'status': 'error', 'message': 'Playlist name is required'}, status=400)
    p = Playlist.objects.create(user=request.user, name=name)
    return JsonResponse({'status': 'success', 'id': p.id, 'name': p.name})


@login_required(login_url='login')
@require_POST
def record_play(request):
    song_id = request.POST.get('song_id')
    if song_id:
        Song.objects.filter(id=song_id).update(play_count=F('play_count') + 1)
    return JsonResponse({'status': 'recorded'})


# ---------------------------------------------------------------------------
# Admin Panel Views
# ---------------------------------------------------------------------------

def admin_required(view_func):
    @login_required(login_url='admin_login')
    @functools.wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Administrator privilege required.")
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped


def admin_login(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_dashboard')

    if request.method == "POST":
        login_input = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user_obj = None
        if '@' in login_input:
            user_obj = User.objects.filter(email__iexact=login_input).first()
        else:
            user_obj = User.objects.filter(username__iexact=login_input).first()

        user = authenticate(request, username=user_obj.username, password=password) if user_obj else None
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            messages.success(request, f"Welcome to Admin Console, {user.username}!")
            return redirect('admin_dashboard')
        messages.error(request, "Invalid administrator credentials.")

    return render(request, "admin/auth/admin_login.html")


@admin_required
def admin_logout(request):
    logout(request)
    messages.info(request, "Logged out of admin console.")
    return redirect('admin_login')


@admin_required
def admin_dashboard(request):
    total_users = User.objects.count()
    premium_users = User.objects.filter(is_premium=True).count()
    total_songs = Song.objects.count()
    public_songs = Song.objects.filter(is_public=True).count()
    user_uploads = Song.objects.filter(uploaded_by__isnull=False, uploaded_by__is_staff=False).count()
    premium_songs_count = Song.objects.filter(is_premium=True).count()
    total_playlists = Playlist.objects.count()

    recent_songs = Song.objects.order_by('-created_at')[:5]
    most_played = Song.objects.order_by('-play_count', '-created_at')[:5]

    top_artists = Song.objects.values('artist').annotate(
        song_count=Count('id')
    ).order_by('-song_count')[:4]
    recent_artists = []
    for item in top_artists:
        song = Song.objects.filter(artist=item['artist']).order_by('-created_at').first()
        recent_artists.append({
            'name': item['artist'],
            'song_count': item['song_count'],
            'image': song.cover_url if song else f"{settings.STATIC_URL}artists/default.jpg",
        })

    context = {
        "total_users": total_users,
        "premium_users": premium_users,
        "total_songs": total_songs,
        "public_songs": public_songs,
        "user_uploads": user_uploads,
        "premium_songs_count": premium_songs_count,
        "total_playlists": total_playlists,
        "recent_songs": recent_songs,
        "recent_artists": recent_artists,
        "most_played": most_played,
    }
    return render(request, "admin/layout/admin_dashboard.html", context)


@admin_required
def admin_songs(request):
    search = request.GET.get('search', '').strip()
    filter_type = request.GET.get('filter', 'all')  # all, public, user_uploads, premium, free, audio, video

    songs = Song.objects.select_related('uploaded_by').order_by('-created_at')
    if search:
        songs = songs.filter(Q(title__icontains=search) | Q(artist__icontains=search) | Q(album__icontains=search))

    if filter_type == 'public':
        songs = songs.filter(is_public=True)
    elif filter_type == 'user_uploads':
        songs = songs.filter(uploaded_by__isnull=False, uploaded_by__is_staff=False)
    elif filter_type == 'premium':
        songs = songs.filter(is_premium=True)
    elif filter_type == 'free':
        songs = songs.filter(is_premium=False)
    elif filter_type == 'video':
        songs = songs.filter(media_type='video')
    elif filter_type == 'audio':
        songs = songs.filter(media_type='audio')

    page_obj = Paginator(songs, 12).get_page(request.GET.get('page'))
    return render(request, "admin/songs/admin_songs.html", {
        "songs": page_obj,
        "search_query": search,
        "filter_type": filter_type,
    })


@admin_required
def add_song(request):
    """Admin Add Song: Allows unlimited song additions, marking as Premium/Free, Public/Private."""
    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        artist = request.POST.get('artist', '').strip()
        genre = request.POST.get('genre', 'Other')
        release_date = request.POST.get('release_date') or timezone.now().date()
        media_type = request.POST.get('media_type', 'audio')
        youtube_url = request.POST.get('youtube_url', '').strip()
        duration_str = request.POST.get('duration', '')
        is_premium = request.POST.get('is_premium') == 'on' or request.POST.get('is_premium') == 'True'
        is_public = request.POST.get('is_public') == 'on' or request.POST.get('is_public') == 'True'
        lyrics = request.POST.get('lyrics', '').strip()

        youtube_id = extract_youtube_id(youtube_url) if youtube_url else None
        info = get_youtube_info(youtube_id) if youtube_id else None

        title = title or (info or {}).get('title') or "Untitled Song"
        artist = artist or (info or {}).get('artist') or "Unknown Artist"
        duration = parse_duration_str(duration_str) or (info or {}).get('duration')
        album = request.POST.get('album', '').strip() or ((info or {}).get('album') if info else None)

        song = Song.objects.create(
            title=title,
            artist=artist,
            album=album,
            genre=genre,
            release_date=release_date,
            duration=duration,
            media_type=media_type,
            youtube_id=youtube_id,
            uploaded_by=request.user,
            is_premium=is_premium,
            is_public=is_public,
            lyrics=lyrics,
        )

        # Handle file upload or youtube download
        if 'audio_file' in request.FILES:
            song.audio_file = request.FILES['audio_file']
            song.save()
        elif youtube_id:
            media_path = download_media(youtube_id, media_type)
            if media_path:
                song.audio_file.name = media_path
                song.save()

        # Handle cover image
        if 'cover_image' in request.FILES:
            song.cover_image = request.FILES['cover_image']
            song.save()
        elif youtube_id:
            cover_path = download_thumbnail(youtube_id, (info or {}).get('thumbnail'))
            if cover_path:
                song.cover_image.name = cover_path
                song.save()

        messages.success(request, f"Song '{title}' ({'Premium' if is_premium else 'Free'}) added successfully!")
        return redirect('admin_songs')

    genres = [g[0] for g in Song.GENRE_CHOICES]
    return render(request, "admin/songs/add_song.html", {"genres": genres})


@admin_required
def edit_song(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    if request.method == "POST":
        song.title = request.POST.get('title', song.title or '').strip()
        song.artist = request.POST.get('artist', song.artist or '').strip()
        song.album = request.POST.get('album', song.album or '').strip()
        song.genre = request.POST.get('genre', song.genre)
        song.is_premium = request.POST.get('is_premium') == 'on' or request.POST.get('is_premium') == 'True'
        song.is_public = request.POST.get('is_public') == 'on' or request.POST.get('is_public') == 'True'
        song.lyrics = request.POST.get('lyrics', song.lyrics or '')

        duration_str = request.POST.get('duration')
        if duration_str:
            song.duration = parse_duration_str(duration_str)

        if 'audio_file' in request.FILES:
            song.audio_file = request.FILES['audio_file']
        if 'cover_image' in request.FILES:
            song.cover_image = request.FILES['cover_image']

        song.save()
        messages.success(request, f"Song '{song.title}' updated successfully!")
        return redirect('admin_songs')

    genres = [g[0] for g in Song.GENRE_CHOICES]
    return render(request, "admin/songs/edit_song.html", {"song": song, "genres": genres})


@admin_required
@require_POST
def delete_song(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    title = song.title
    song.delete()
    messages.success(request, f"Song '{title}' deleted permanently.")
    return redirect('admin_songs')


@admin_required
def admin_users(request):
    search = request.GET.get('search', '').strip()
    users = User.objects.annotate(upload_count=Count('uploaded_songs')).order_by('-date_joined')
    if search:
        users = users.filter(Q(username__icontains=search) | Q(email__icontains=search) | Q(user_phone__icontains=search))

    page_obj = Paginator(users, 10).get_page(request.GET.get('page'))
    return render(request, "admin/users/admin_users.html", {
        "users": page_obj,
        "search_query": search,
    })


@admin_required
def add_user(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        phone = request.POST.get('user_phone', '').strip()
        is_staff = request.POST.get('is_staff') == 'on'
        is_premium = request.POST.get('is_premium') == 'on'

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Username already exists.")
        elif email and User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email already exists.")
        elif not password:
            messages.error(request, "Password is required.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.user_phone = phone
            user.is_staff = is_staff
            user.is_premium = is_premium
            if is_premium:
                user.premium_expiry = timezone.now() + timedelta(days=365)
            if 'profile_picture' in request.FILES:
                user.profile_pic = request.FILES['profile_picture']
            user.save()
            messages.success(request, f"User '{username}' created successfully!")
            return redirect('admin_users')

    return render(request, "admin/users/user_add.html")


@admin_required
def edit_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        user.username = request.POST.get('username', user.username).strip()
        user.email = request.POST.get('email', user.email).strip()
        user.user_phone = request.POST.get('user_phone', user.user_phone).strip()
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_premium = request.POST.get('is_premium') == 'on'

        if user.is_premium and not user.premium_expiry:
            user.premium_expiry = timezone.now() + timedelta(days=365)

        if 'profile_picture' in request.FILES:
            user.profile_pic = request.FILES['profile_picture']

        password = request.POST.get('password', '').strip()
        if password:
            user.set_password(password)

        user.save()
        messages.success(request, f"User '{user.username}' updated successfully!")
        return redirect('admin_users')

    return render(request, "admin/users/user_edit.html", {"user": user})


@admin_required
@require_POST
def admin_toggle_premium(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_premium = not user.is_premium
    if user.is_premium:
        user.premium_expiry = timezone.now() + timedelta(days=365)
        status_msg = f"Granted VIP Premium to '{user.username}' (Unlimited Uploads enabled)."
    else:
        user.premium_expiry = None
        status_msg = f"Revoked VIP Premium from '{user.username}' (Standard 20 song limit)."
    user.save()
    messages.success(request, status_msg)
    return redirect('admin_users')


@admin_required
@require_POST
def delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user == request.user:
        messages.error(request, "You cannot delete your own admin account.")
    else:
        username = user.username
        user.delete()
        messages.success(request, f"User '{username}' deleted successfully.")
    return redirect('admin_users')


@admin_required
def admin_video(request):
    search = request.GET.get('search', '').strip()
    videos = Song.objects.filter(media_type='video').order_by('-created_at')
    if search:
        videos = videos.filter(Q(title__icontains=search) | Q(artist__icontains=search))
    page_obj = Paginator(videos, 10).get_page(request.GET.get('page'))
    return render(request, "admin/videos/admin_videos.html", {
        "videos": page_obj,
        "search_query": search,
    })
