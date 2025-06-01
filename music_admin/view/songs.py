from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from music_admin.models import Song
from django.views.decorators.http import require_http_methods

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
        title = request.POST.get('title')
        artist = request.POST.get('artist')
        genre = request.POST.get('genre')
        release_date = request.POST.get('release_date')
        duration = request.POST.get('duration')
        audio_file = request.FILES.get('audio_file')

        if not title or not artist or not genre or not release_date or not duration or not audio_file:
            messages.error(request, "All fields are required.")
            return render(request, "admin/songs/add_song.html")

        try:
            from datetime import timedelta
            # Parse duration string "HH:MM:SS"
            h, m, s = map(int, duration.split(":"))
            duration_td = timedelta(hours=h, minutes=m, seconds=s)

            song = Song(
                title=title,
                artist=artist,
                genre=genre,
                release_date=release_date,
                duration=duration_td,
                audio_file=audio_file,
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

        if not title or not artist:
            messages.error(request, "Title and Artist are required.")
            return render(request, "admin/songs/edit_song.html", {"song": song})

        song.title = title
        song.artist = artist
        if audio_file:
            song.audio_file = audio_file

        try:
            song.full_clean()
            song.save()
            messages.success(request, "Song updated successfully.")
            return redirect("admin_songs")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

    # For previewing audio in the edit form
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