from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from music_admin.models import Song
from django.views.decorators.http import require_http_methods
from django.conf import settings
import yt_dlp
import os

def admin_songs(request):
    search_query = request.GET.get('search', '')
    songs_queryset = Song.objects.all().order_by('-created_at')
    if search_query:
        songs_queryset = songs_queryset.filter(
            Q(title__icontains=search_query) | Q(artist__icontains=search_query)
        )
    for song in songs_queryset:
        if song.audio_file:
            song.audio_url = song.audio_file.url
        else:
            song.audio_url = ""
    context = {
        'songs': songs_queryset,
        'search_query': search_query,
    }
    return render(request, 'admin/songs/admin_songs.html', context)

@require_http_methods(["GET", "POST"])
def add_song(request):
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

        # If YouTube URL is provided, use yt-dlp to fetch and fill details
        if youtube_url:
            try:
                output_dir = os.path.join(settings.MEDIA_ROOT, 'songs')
                os.makedirs(output_dir, exist_ok=True)
                ydl_opts = {
                    'format': 'bestaudio/best' if media_type == 'audio' else 'bestvideo+bestaudio/best',
                    'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }] if media_type == 'audio' else [],
                    'writethumbnail': True,
                    'writeinfojson': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)
                # Get file path
                if media_type == 'audio':
                    ext = 'mp3'
                else:
                    ext = info.get('ext', 'mp4')
                file_title = info.get('title', 'unknown')
                file_path = os.path.join('songs', f"{file_title}.{ext}")
                abs_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
                # Get file size
                file_size = os.path.getsize(abs_file_path) if os.path.exists(abs_file_path) else 0
                # Get cover image path if downloaded
                thumbnail_url = info.get('thumbnail')
                # Try to get metadata
                title = info.get('title', title)
                artist = info.get('artist', artist) or info.get('uploader', artist)
                genre = info.get('genre', genre)
                release_date = info.get('release_date', release_date)
                if release_date and len(release_date) == 8:
                    release_date = f"{release_date[:4]}-{release_date[4:6]}-{release_date[6:]}"
                duration_seconds = info.get('duration')
                if duration_seconds:
                    from datetime import timedelta
                    duration_td = timedelta(seconds=duration_seconds)
                else:
                    # fallback to form
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
                )
                song.full_clean()
                song.save()
                messages.success(request, "Song added successfully from YouTube.")
                return redirect("admin_songs")
            except Exception as e:
                messages.error(request, f"Error downloading from YouTube: {e}")
                return render(request, "admin/songs/add_song.html")
        else:
            # Manual upload
            if not title or not artist or not genre or not release_date or not duration or not audio_file or not media_type:
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
                return redirect("admin_songs")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")

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