from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    user_phone = models.CharField(max_length=20, null=True, blank=True)
    profile_pic = models.ImageField(upload_to='profile/', blank=True, null=True, default='images/img.png')
    is_premium = models.BooleanField(default=False, help_text="Designates whether the user has active Premium VIP status.")
    premium_expiry = models.DateTimeField(null=True, blank=True, help_text="Expiry date for premium subscription.")

    @property
    def is_vip(self):
        if self.is_superuser or self.is_staff:
            return True
        if self.is_premium:
            if self.premium_expiry and self.premium_expiry < timezone.now():
                return False
            return True
        return False

    @property
    def uploaded_count(self):
        return self.uploaded_songs.count()

    @property
    def upload_limit(self):
        if self.is_vip:
            return None  # Unlimited
        return 20

    @property
    def uploads_remaining(self):
        if self.is_vip:
            return "Unlimited"
        return max(0, 20 - self.uploaded_count)

    @property
    def upload_percentage(self):
        if self.is_vip:
            return 100
        return min(100, int((self.uploaded_count / 20) * 100))

    def can_upload(self):
        if self.is_vip:
            return True
        return self.uploaded_count < 20

    def __str__(self):
        return self.username


class Song(models.Model):
    GENRE_CHOICES = [
        ("Pop", "Pop"),
        ("Rock", "Rock"),
        ("Hip-Hop", "Hip-Hop"),
        ("Jazz", "Jazz"),
        ("Classical", "Classical"),
        ("Lofi", "Lofi"),
        ("Electronic", "Electronic"),
        ("R&B", "R&B"),
        ("Country", "Country"),
        ("Acoustic", "Acoustic"),
        ("Other", "Other"),
    ]

    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    album = models.CharField(max_length=255, blank=True, null=True)
    genre = models.CharField(max_length=100, choices=GENRE_CHOICES, default="Other")
    release_date = models.DateField(null=True, blank=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    audio_file = models.FileField(upload_to='songs/', max_length=255, blank=True, null=True)
    duration = models.DurationField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    media_type = models.CharField(max_length=10, choices=[('audio', 'Audio'), ('video', 'Video')], default='audio')
    youtube_id = models.CharField(max_length=64, blank=True, null=True, db_index=True)

    # Multi-tier ownership and permissions
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_songs'
    )
    is_premium = models.BooleanField(
        default=False, help_text="True if this is a Premium VIP track that requires premium access."
    )
    is_public = models.BooleanField(
        default=True, help_text="True for admin/public songs visible to everyone; False for private user uploads."
    )
    play_count = models.PositiveIntegerField(default=0)
    lyrics = models.TextField(blank=True, null=True)

    @property
    def audio_url(self):
        if self.audio_file:
            return self.audio_file.url
        return ""

    @property
    def cover_url(self):
        if self.cover_image:
            return self.cover_image.url
        if self.youtube_id:
            return f"https://img.youtube.com/vi/{self.youtube_id}/hqdefault.jpg"
        return "/static/artists/default.jpg"

    @property
    def formatted_duration(self):
        if not self.duration:
            return "0:00"
        total_seconds = int(self.duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"

    @property
    def is_user_upload(self):
        return self.uploaded_by is not None and not (self.uploaded_by.is_staff or self.uploaded_by.is_superuser)

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
