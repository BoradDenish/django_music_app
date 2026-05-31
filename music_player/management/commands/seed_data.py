import datetime
from django.core.management.base import BaseCommand
from music_player.models import User, Song, Playlist, FavoriteSong
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seeds the database with initial data for the new music_player app'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # 1. Create Test User
        test_user, created = User.objects.get_or_create(
            username='user',
            defaults={
                'email': 'user@example.com',
                'first_name': 'Test',
                'last_name': 'User',
            }
        )
        if created:
            test_user.set_password('user123')
            test_user.save()
            self.stdout.write(f'Created test user: {test_user.username}')

        # 2. Create Songs
        songs_data = [
            {
                'title': '7 Rings',
                'artist': 'Ariana Grande',
                'album': 'Thank U, Next',
                'genre': 'Pop',
                'release_date': '2019-01-18',
                'duration': datetime.timedelta(minutes=2, seconds=58),
                'cover_image': 'artists/ariana-grande.avif',
                'media_type': 'audio'
            },
            {
                'title': 'Dynamite',
                'artist': 'BTS',
                'album': 'Be',
                'genre': 'Pop',
                'release_date': '2020-08-21',
                'duration': datetime.timedelta(minutes=3, seconds=19),
                'cover_image': 'artists/BTS.jpg',
                'media_type': 'audio'
            },
            {
                'title': 'God\'s Plan',
                'artist': 'Drake',
                'album': 'Scorpion',
                'genre': 'Hip-Hop',
                'release_date': '2018-01-19',
                'duration': datetime.timedelta(minutes=3, seconds=18),
                'cover_image': 'artists/Drake.jpg',
                'media_type': 'audio'
            },
            {
                'title': 'Levitating',
                'artist': 'Dua Lipa',
                'album': 'Future Nostalgia',
                'genre': 'Pop',
                'release_date': '2020-03-27',
                'duration': datetime.timedelta(minutes=3, seconds=23),
                'cover_image': 'artists/dua-lipa.jpg',
                'media_type': 'audio'
            },
            {
                'title': 'Shape of You',
                'artist': 'Ed Sheeran',
                'album': '÷',
                'genre': 'Pop',
                'release_date': '2017-01-06',
                'duration': datetime.timedelta(minutes=3, seconds=53),
                'cover_image': 'artists/Ed-Sheeran.jpg',
                'media_type': 'audio'
            },
            {
                'title': 'Blinding Lights',
                'artist': 'The Weeknd',
                'album': 'After Hours',
                'genre': 'Electronic',
                'release_date': '2019-11-29',
                'duration': datetime.timedelta(minutes=3, seconds=20),
                'cover_image': 'artists/The-Weeknd.png',
                'media_type': 'audio'
            },
        ]

        created_songs = []
        for data in songs_data:
            song, created = Song.objects.get_or_create(
                title=data['title'],
                artist=data['artist'],
                defaults=data
            )
            created_songs.append(song)
            if created:
                self.stdout.write(f'Created song: {song.title}')

        # 3. Create Playlists
        playlist, created = Playlist.objects.get_or_create(
            user=test_user,
            name='My Favorites',
            defaults={'description': 'My favorite pop songs'}
        )
        if created:
            playlist.songs.set(created_songs[:3])
            self.stdout.write(f'Created playlist: {playlist.name}')

        # 4. Create Favorite Songs
        for song in created_songs[3:]:
            FavoriteSong.objects.get_or_create(user=test_user, song=song)
            self.stdout.write(f'Favorited song: {song.title} for user: {test_user.username}')

        self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))
