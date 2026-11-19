from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Song, Playlist, FavoriteSong


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'user_phone', 'is_vip_badge',
        'is_premium', 'premium_expiry', 'is_staff', 'is_superuser'
    )
    list_filter = ('is_premium', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'user_phone')
    ordering = ('username',)
    fieldsets = UserAdmin.fieldsets + (
        ('MusicApp Extra Info', {
            'fields': ('user_phone', 'profile_pic', 'is_premium', 'premium_expiry')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('MusicApp Extra Info', {
            'fields': ('user_phone', 'profile_pic', 'is_premium', 'premium_expiry')
        }),
    )

    @admin.display(description='VIP Status')
    def is_vip_badge(self, obj):
        return "VIP" if obj.is_vip else "Standard"


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'artist', 'genre', 'media_type',
        'is_premium', 'is_public', 'play_count', 'uploaded_by', 'created_at'
    )
    list_filter = ('genre', 'media_type', 'is_premium', 'is_public', 'created_at')
    search_fields = ('title', 'artist', 'album', 'youtube_id')
    ordering = ('-created_at',)
    readonly_fields = ('play_count', 'created_at')
    fieldsets = (
        ('Track Information', {
            'fields': ('title', 'artist', 'album', 'genre', 'release_date', 'duration')
        }),
        ('Media Content', {
            'fields': ('media_type', 'audio_file', 'cover_image', 'youtube_id')
        }),
        ('Access & Ownership', {
            'fields': ('uploaded_by', 'is_premium', 'is_public', 'play_count', 'created_at')
        }),
        ('Lyrics', {
            'fields': ('lyrics',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'song_count', 'created_at', 'updated_at')
    search_fields = ('name', 'user__username', 'description')
    list_filter = ('created_at', 'updated_at')
    filter_horizontal = ('songs',)

    @admin.display(description='Songs Count')
    def song_count(self, obj):
        return obj.songs.count()


@admin.register(FavoriteSong)
class FavoriteSongAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'created_at')
    search_fields = ('user__username', 'song__title', 'song__artist')
    list_filter = ('created_at',)
    raw_id_fields = ('user', 'song')
