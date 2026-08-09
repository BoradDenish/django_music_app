from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    user_phone = models.CharField(max_length=20, null=True, blank=True)
    profile_pic = models.ImageField(upload_to='profile/', blank=True, null=True, default='images/img.png')
    
    def __str__(self):
        return self.username

class Song(models.Model):
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    album = models.CharField(max_length=255, blank=True, null=True)
    genre = models.CharField(max_length=100, choices=[
        ("Pop", "Pop"),
        ("Rock", "Rock"),
        ("Hip-Hop", "Hip-Hop"),
        ("Jazz", "Jazz"),
        ("Classical", "Classical"),
        ("Electronic", "Electronic"),
        ("Other", "Other"),
    ])
    release_date = models.DateField()
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    audio_file = models.FileField(upload_to='songs/', max_length=255, blank=True, null=True)
    duration = models.DurationField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    media_type = models.CharField(max_length=10, choices=[('audio', 'Audio'), ('video', 'Video')], default='audio')
    youtube_id = models.CharField(max_length=32, blank=True, null=True, unique=True)

    @property
    def audio_url(self):
        if self.audio_file:
            return self.audio_file.url
        return ""

    def __str__(self):
        return f"{self.title} - {self.artist}"

class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    songs = models.ManyToManyField(Song, related_name='playlists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class FavoriteSong(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'song')

    def __str__(self):
        return f"{self.user.username} - {self.song.title}"
