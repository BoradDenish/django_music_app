from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from music_admin.models import Song
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.templatetags.static import static
import yt_dlp
import os
import logging
import re
import shutil

# Logging setup for songs.py
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log')
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger('songs_logger')
handler = logging.FileHandler(os.path.join(LOG_DIR, 'songs.log'))
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

MAX_AUDIO_FILE_LENGTH = 255  # or whatever your model allows

def admin_songs(request):
    search_query = request.GET.get('search', '')
    songs_queryset = Song.objects.all().order_by('-created_at')
    if search_query:
        songs_queryset = songs_queryset.filter(
            Q(title__icontains=search_query) | Q(artist__icontains=search_query)
        )
    for song in songs_queryset:
        # If audio_file is a FileField and has a url
        if hasattr(song.audio_file, 'url'):
            song.audio_url = song.audio_file.url
        # If audio_file is a string path (e.g., 'songs/filename.mp3')
        elif song.audio_file:
            # Convert backslashes to forward slashes for URL
            audio_path = str(song.audio_file).replace('\\', '/')
            song.audio_url = settings.MEDIA_URL + audio_path
        else:
            song.audio_url = ""
    context = {
        'songs': songs_queryset,
        'search_query': search_query,
    }
    print("Files in media/songs:", os.listdir(os.path.join(settings.MEDIA_ROOT, 'songs')))
    return render(request, 'admin/songs/admin_songs.html', context)

@require_http_methods(["GET", "POST"])
def add_song(request):
    logger.info("add_song called by user: %s", request.user if hasattr(request, 'user') else 'anonymous')
    if request.method == "POST":
        youtube_url = request.POST.get('youtube_url', '').strip()
        media_type = request.POST.get('media_type', '').strip()
        title = request.POST.get('title')
        artist = request.POST.get('artist')
        genre = request.POST.get('genre')
        release_date = request.POST.get('release_date')
        duration = request.POST.get('duration')
        audio_file = request.FILES.get('audio_file')
        cover_image = None

        if youtube_url:
            try:
                # Extract YouTube video ID using yt_dlp
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info_dict = ydl.extract_info(youtube_url, download=False)
                    youtube_id = info_dict.get('id')
                # Check if this YouTube video is already in the DB
                existing_song = Song.objects.filter(youtube_id=youtube_id).first()
                if existing_song:
                    messages.warning(request, "This YouTube song already exists in the database.")
                    return redirect("admin_songs")

                output_dir = os.path.join(settings.MEDIA_ROOT, 'songs')
                os.makedirs(output_dir, exist_ok=True)

                # Always use YouTube ID for filename
                ext = 'mp3' if media_type == 'audio' else info_dict.get('ext', 'mp4')
                safe_filename = f"{youtube_id}.{ext}"

                ydl_opts = {
                    'format': 'bestaudio/best' if media_type == 'audio' else 'bestvideo+bestaudio/best',
                    'outtmpl': os.path.join(output_dir, safe_filename),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }] if media_type == 'audio' else [],
                    'writethumbnail': True,
                    'writeinfojson': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)

                file_path = os.path.join('songs', safe_filename)
                if len(file_path) > MAX_AUDIO_FILE_LENGTH:
                    file_path = file_path[:MAX_AUDIO_FILE_LENGTH]
                abs_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
                thumbnail_url = info.get('thumbnail')
                title = info.get('title') or title or 'Unknown Title'
                artist = info.get('artist') or info.get('uploader') or artist or 'Unknown Artist'
                genre = info.get('genre') or genre or 'Unknown Genre'
                release_date = info.get('release_date', release_date)
                if release_date and len(release_date) == 8:
                    release_date = f"{release_date[:4]}-{release_date[4:6]}-{release_date[6:]}"
                duration_seconds = info.get('duration')
                if duration_seconds:
                    from datetime import timedelta
                    duration_td = timedelta(seconds=duration_seconds)
                else:
                    h, m, s = map(int, (duration or "0:0:0").split(":"))
                    from datetime import timedelta
                    duration_td = timedelta(hours=h, minutes=m, seconds=s)
                # Save Song instance
                song = Song(
                    title=title,
                    artist=artist,
                    genre=genre,
                    release_date=release_date,
                    duration=duration_td,
                    audio_file=file_path,
                    cover_image=thumbnail_url,
                    media_type=media_type,
                    youtube_id=youtube_id,
                )
                song.full_clean()
                song.save()
                messages.success(request, "Song added successfully from YouTube.")
                logger.info("Song added from YouTube: %s by %s", title, artist)
                return redirect("admin_songs")
            except Exception as e:
                messages.error(request, f"Error downloading from YouTube: {e}")
                logger.error("Error downloading from YouTube: %s", e)
                return render(request, "admin/songs/add_song.html")
        else:
            # Manual upload
            if not title or not artist or not genre or not release_date or not duration or not audio_file or not media_type:
                logger.warning("Missing fields in manual song upload")
                messages.error(request, "All fields are required.")
                return render(request, "admin/songs/add_song.html")
            try:
                from datetime import timedelta
                h, m, s = map(int, duration.split(":"))
                duration_td = timedelta(hours=h, minutes=m, seconds=s)
                song = Song(
                    title=title,
                    artist=artist,
                    genre=genre,
                    release_date=release_date,
                    duration=duration_td,
                    audio_file=audio_file,
                    media_type=media_type,
                )
                song.full_clean()
                song.save()
                messages.success(request, "Song added successfully.")
                logger.info("Song added manually: %s by %s", title, artist)
                return redirect("admin_songs")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
                logger.error("Error adding song manually: %s", e)

    return render(request, "admin/songs/add_song.html")

@require_http_methods(["GET", "POST"])
def edit_song(request, song_id):
    song = get_object_or_404(Song, pk=song_id)

    if request.method == "POST":
        title = request.POST.get('title')
        artist = request.POST.get('artist')
        audio_file = request.FILES.get('audio_file')
        media_type = request.POST.get('media_type', song.media_type)

        if not title or not artist:
            messages.error(request, "Title and Artist are required.")
            return render(request, "admin/songs/edit_song.html", {"song": song})

        song.title = title
        song.artist = artist
        song.media_type = media_type
        if audio_file:
            song.audio_file = audio_file

        try:
            song.full_clean()
            song.save()
            messages.success(request, "Song updated successfully.")
            return redirect("admin_songs")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            logger.error(f"An error occurred: {e}")

    song.audio_url = song.audio_file.url if song.audio_file else ""
    return render(request, "admin/songs/edit_song.html", {"song": song})

@require_http_methods(["POST"])
def delete_song(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    try:
        song.delete()
        messages.success(request, "Song deleted successfully.")
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        logger.error(f"An error occurred: {e}")
    return redirect("admin_songs")

def download_youtube_audio(youtube_url, output_dir):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'writethumbnail': True,
        'writeinfojson': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        return info