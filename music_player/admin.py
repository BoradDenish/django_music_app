from django.contrib import admin
from .models import User, Song, Playlist, FavoriteSong

admin.site.register(User)
admin.site.register(Song)
admin.site.register(Playlist)
admin.site.register(FavoriteSong)
