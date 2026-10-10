import datetime
from django.core.management.base import BaseCommand
from music_player.models import User, Song, Playlist, FavoriteSong

class Command(BaseCommand):
    help = 'Seeds the database with full dummy data across all tables for MusicApp'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting data seeding...')

        # Clean up legacy broken songs without youtube_id or local audio
        deleted_count, _ = Song.objects.filter(youtube_id__isnull=True, audio_file='').delete()
        if deleted_count:
            self.stdout.write(f"Cleaned up {deleted_count} broken legacy songs.")

        # -------------------------------------------------------------------
        # 1. USERS TABLE SEEDING
        # -------------------------------------------------------------------
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@musicapp.com',
                'first_name': 'System',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
                'user_phone': '+1 555-010-0000',
                'password': 'admin123'
            },
            {
                'username': 'user',
                'email': 'user@musicapp.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_staff': False,
                'is_superuser': False,
                'user_phone': '+1 555-019-2834',
                'password': 'user123'
            },
            {
                'username': 'john_doe',
                'email': 'john@musicapp.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'is_staff': False,
                'is_superuser': False,
                'user_phone': '+1 555-014-9912',
                'password': 'user123'
            },
            {
                'username': 'emily_w',
                'email': 'emily@musicapp.com',
                'first_name': 'Emily',
                'last_name': 'Watson',
                'is_staff': False,
                'is_superuser': False,
                'user_phone': '+1 555-018-4421',
                'password': 'user123'
            },
            {
                'username': 'alex_r',
                'email': 'alex@musicapp.com',
                'first_name': 'Alex',
                'last_name': 'Rivera',
                'is_staff': False,
                'is_superuser': False,
                'user_phone': '+1 555-016-3390',
                'password': 'user123'
            },
            {
                'username': 'sophia_c',
                'email': 'sophia@musicapp.com',
                'first_name': 'Sophia',
                'last_name': 'Chen',
                'is_staff': False,
                'is_superuser': False,
                'user_phone': '+1 555-017-8833',
                'password': 'user123'
            },
            {
                'username': 'marcus_v',
                'email': 'marcus@musicapp.com',
                'first_name': 'Marcus',
                'last_name': 'Vance',
                'is_staff': False,
                'is_superuser': False,
                'user_phone': '+1 555-012-7711',
                'password': 'user123'
            },
        ]

        users_dict = {}
        for udata in users_data:
            pwd = udata.pop('password')
            user, created = User.objects.get_or_create(
                username=udata['username'],
                defaults=udata
            )
            if created:
                user.set_password(pwd)
                user.save()
                self.stdout.write(f"Created User: {user.username}")
            else:
                # Update flags if user exists
                user.email = udata['email']
                user.is_staff = udata['is_staff']
                user.is_superuser = udata['is_superuser']
                user.set_password(pwd)
                user.save()
            users_dict[user.username] = user

        # -------------------------------------------------------------------
        # 2. SONGS TABLE SEEDING (Audio & Video)
        # -------------------------------------------------------------------
        songs_data = [
            # Pop Audio
            {
                'title': '7 Rings',
                'artist': 'Ariana Grande',
                'album': 'Thank U, Next',
                'genre': 'Pop',
                'release_date': '2019-01-18',
                'duration': datetime.timedelta(minutes=2, seconds=58),
                'cover_image': 'artists/ariana-grande.avif',
                'media_type': 'audio',
                'youtube_id': 'QYh6mYIJG2Y'
            },
            {
                'title': 'Dynamite',
                'artist': 'BTS',
                'album': 'Be',
                'genre': 'Pop',
                'release_date': '2020-08-21',
                'duration': datetime.timedelta(minutes=3, seconds=19),
                'cover_image': 'artists/BTS.jpg',
                'media_type': 'audio',
                'youtube_id': 'gdZLi9oWNZg'
            },
            {
                'title': 'Levitating',
                'artist': 'Dua Lipa',
                'album': 'Future Nostalgia',
                'genre': 'Pop',
                'release_date': '2020-03-27',
                'duration': datetime.timedelta(minutes=3, seconds=23),
                'cover_image': 'artists/dua-lipa.jpg',
                'media_type': 'audio',
                'youtube_id': 'dHXC_2N1Z4U'
            },
            {
                'title': 'Shape of You',
                'artist': 'Ed Sheeran',
                'album': '÷',
                'genre': 'Pop',
                'release_date': '2017-01-06',
                'duration': datetime.timedelta(minutes=3, seconds=53),
                'cover_image': 'artists/Ed-Sheeran.jpg',
                'media_type': 'audio',
                'youtube_id': 'JGwWNGJdvx8'
            },
            {
                'title': 'As It Was',
                'artist': 'Harry Styles',
                'album': "Harry's House",
                'genre': 'Pop',
                'release_date': '2022-04-01',
                'duration': datetime.timedelta(minutes=2, seconds=47),
                'cover_image': 'covers/as_it_was.jpg',
                'media_type': 'audio',
                'youtube_id': 'H5v3kku4y6Q'
            },
            # Hip-Hop Audio
            {
                'title': "God's Plan",
                'artist': 'Drake',
                'album': 'Scorpion',
                'genre': 'Hip-Hop',
                'release_date': '2018-01-19',
                'duration': datetime.timedelta(minutes=3, seconds=18),
                'cover_image': 'artists/Drake.jpg',
                'media_type': 'audio',
                'youtube_id': 'xpVfcZ0ZcFM'
            },
            {
                'title': 'Sunflower',
                'artist': 'Post Malone & Swae Lee',
                'album': 'Spider-Man: Into the Spider-Verse',
                'genre': 'Hip-Hop',
                'release_date': '2018-10-18',
                'duration': datetime.timedelta(minutes=2, seconds=38),
                'cover_image': 'covers/sunflower.jpg',
                'media_type': 'audio',
                'youtube_id': 'ApXoWvfEYVU'
            },
            {
                'title': 'Sicko Mode',
                'artist': 'Travis Scott',
                'album': 'Astroworld',
                'genre': 'Hip-Hop',
                'release_date': '2018-08-03',
                'duration': datetime.timedelta(minutes=5, seconds=12),
                'cover_image': 'covers/sicko_mode.jpg',
                'media_type': 'audio',
                'youtube_id': '6ONRf7h3Mdk'
            },
            # Electronic Audio
            {
                'title': 'Blinding Lights',
                'artist': 'The Weeknd',
                'album': 'After Hours',
                'genre': 'Electronic',
                'release_date': '2019-11-29',
                'duration': datetime.timedelta(minutes=3, seconds=20),
                'cover_image': 'artists/The-Weeknd.png',
                'media_type': 'audio',
                'youtube_id': '4NRXx6U8ABQ'
            },
            {
                'title': 'Starboy',
                'artist': 'The Weeknd ft. Daft Punk',
                'album': 'Starboy',
                'genre': 'Electronic',
                'release_date': '2016-09-21',
                'duration': datetime.timedelta(minutes=3, seconds=50),
                'cover_image': 'artists/The-Weeknd.png',
                'media_type': 'audio',
                'youtube_id': '34Na4j8AVgA'
            },
            {
                'title': 'Midnight City',
                'artist': 'M83',
                'album': "Hurry Up, We're Dreaming",
                'genre': 'Electronic',
                'release_date': '2011-08-16',
                'duration': datetime.timedelta(minutes=4, seconds=3),
                'cover_image': 'covers/midnight_city.jpg',
                'media_type': 'audio',
                'youtube_id': 'dX3k_QDnzHE'
            },
            # Rock Audio
            {
                'title': 'Bohemian Rhapsody',
                'artist': 'Queen',
                'album': 'A Night at the Opera',
                'genre': 'Rock',
                'release_date': '1975-10-31',
                'duration': datetime.timedelta(minutes=5, seconds=55),
                'cover_image': 'covers/queen.jpg',
                'media_type': 'audio',
                'youtube_id': 'fJ9rUzIMcZQ'
            },
            {
                'title': 'Hotel California',
                'artist': 'Eagles',
                'album': 'Hotel California',
                'genre': 'Rock',
                'release_date': '1977-02-22',
                'duration': datetime.timedelta(minutes=6, seconds=30),
                'cover_image': 'covers/eagles.jpg',
                'media_type': 'audio',
                'youtube_id': '09R8_2nJtjg'
            },
            # Jazz & Classical Audio
            {
                'title': 'Take Five',
                'artist': 'Dave Brubeck',
                'album': 'Time Out',
                'genre': 'Jazz',
                'release_date': '1959-09-21',
                'duration': datetime.timedelta(minutes=5, seconds=24),
                'cover_image': 'covers/jazz.jpg',
                'media_type': 'audio',
                'youtube_id': 'vmDDOFXSgAs'
            },
            {
                'title': 'Clair de Lune',
                'artist': 'Claude Debussy',
                'album': 'Suite Bergamasque',
                'genre': 'Classical',
                'release_date': '1905-01-01',
                'duration': datetime.timedelta(minutes=5, seconds=5),
                'cover_image': 'covers/classical.jpg',
                'media_type': 'audio',
                'youtube_id': 'WNcsUNKlAKw'
            },
            # Video Tracks
            {
                'title': 'Bad Guy (Official Music Video)',
                'artist': 'Billie Eilish',
                'album': 'When We All Fall Asleep, Where Do We Go?',
                'genre': 'Pop',
                'release_date': '2019-03-29',
                'duration': datetime.timedelta(minutes=3, seconds=25),
                'cover_image': 'covers/bad_guy.jpg',
                'media_type': 'video',
                'youtube_id': 'DyDfgMOUjCI'
            },
            {
                'title': 'Uptown Funk (Official Video)',
                'artist': 'Mark Ronson ft. Bruno Mars',
                'album': 'Uptown Special',
                'genre': 'Pop',
                'release_date': '2014-11-10',
                'duration': datetime.timedelta(minutes=4, seconds=30),
                'cover_image': 'covers/uptown_funk.jpg',
                'media_type': 'video',
                'youtube_id': 'OPf0YbXqDm0'
            },
            {
                'title': 'Smells Like Teen Spirit (Music Video)',
                'artist': 'Nirvana',
                'album': 'Nevermind',
                'genre': 'Rock',
                'release_date': '1991-09-10',
                'duration': datetime.timedelta(minutes=4, seconds=38),
                'cover_image': 'covers/nirvana.jpg',
                'media_type': 'video',
                'youtube_id': 'hTWKbfoikeg'
            },
            {
                'title': 'Counting Stars (Official Video)',
                'artist': 'OneRepublic',
                'album': 'Native',
                'genre': 'Pop',
                'release_date': '2013-06-14',
                'duration': datetime.timedelta(minutes=4, seconds=19),
                'cover_image': 'covers/counting_stars.jpg',
                'media_type': 'video',
                'youtube_id': 'hT_nvWreIhg'
            },
            {
                'title': 'Closer (Official Video)',
                'artist': 'The Chainsmokers ft. Halsey',
                'album': 'Collage',
                'genre': 'Electronic',
                'release_date': '2016-07-29',
                'duration': datetime.timedelta(minutes=4, seconds=5),
                'cover_image': 'covers/closer.jpg',
                'media_type': 'video',
                'youtube_id': 'PT2_F-1esPk'
            },
        ]

        created_songs_dict = {}
        for sdata in songs_data:
            yt_id = sdata.get('youtube_id')
            song, created = Song.objects.get_or_create(
                youtube_id=yt_id,
                defaults=sdata
            )
            if not created:
                # Update attributes if existing
                for key, val in sdata.items():
                    setattr(song, key, val)
                song.save()
            created_songs_dict[song.title] = song
            self.stdout.write(f"Seeded Song: {song.title} [{song.genre} - {song.media_type}]")

        # -------------------------------------------------------------------
        # 3. PLAYLISTS TABLE SEEDING
        # -------------------------------------------------------------------
        playlists_data = [
            {
                'user': users_dict['user'],
                'name': 'Top Pop Hits 2026',
                'description': 'The biggest chart-topping pop anthems across the globe.',
                'songs': ['7 Rings', 'Dynamite', 'Levitating', 'Shape of You', 'As It Was']
            },
            {
                'user': users_dict['john_doe'],
                'name': 'Classic Rock Anthems',
                'description': 'Timeless rock tracks that defined generations.',
                'songs': ['Bohemian Rhapsody', 'Hotel California', 'Smells Like Teen Spirit (Music Video)']
            },
            {
                'user': users_dict['alex_r'],
                'name': 'Synthwave & Electronic Glow',
                'description': 'Late night driving synths, electronic beats, and retro vibes.',
                'songs': ['Blinding Lights', 'Starboy', 'Midnight City', 'Closer (Official Video)']
            },
            {
                'user': users_dict['emily_w'],
                'name': 'Chill Jazz & Classical Notes',
                'description': 'Relaxing acoustic, piano, and jazz masterpieces for study & relaxation.',
                'songs': ['Take Five', 'Clair de Lune']
            },
            {
                'user': users_dict['marcus_v'],
                'name': 'Hip-Hop Heavy Rotation',
                'description': 'Top hip-hop bangers and lyrical tracks.',
                'songs': ["God's Plan", 'Sunflower', 'Sicko Mode']
            },
            {
                'user': users_dict['sophia_c'],
                'name': 'Video Spotlight Selection',
                'description': 'Visual music video performances in HD.',
                'songs': ['Bad Guy (Official Music Video)', 'Uptown Funk (Official Video)', 'Counting Stars (Official Video)']
            },
        ]

        for pdata in playlists_data:
            song_titles = pdata.pop('songs')
            playlist, created = Playlist.objects.get_or_create(
                user=pdata['user'],
                name=pdata['name'],
                defaults=pdata
            )
            playlist.description = pdata['description']
            playlist.save()

            # Attach songs to playlist
            songs_to_add = [created_songs_dict[st] for st in song_titles if st in created_songs_dict]
            playlist.songs.set(songs_to_add)
            self.stdout.write(f"Seeded Playlist: '{playlist.name}' for user {playlist.user.username} ({playlist.songs.count()} songs)")

        # -------------------------------------------------------------------
        # 4. FAVORITE SONGS TABLE SEEDING
        # -------------------------------------------------------------------
        favorites_data = [
            (users_dict['user'], created_songs_dict['7 Rings']),
            (users_dict['user'], created_songs_dict['Levitating']),
            (users_dict['user'], created_songs_dict['Blinding Lights']),
            (users_dict['user'], created_songs_dict['Bohemian Rhapsody']),
            (users_dict['john_doe'], created_songs_dict['Hotel California']),
            (users_dict['john_doe'], created_songs_dict['Bohemian Rhapsody']),
            (users_dict['emily_w'], created_songs_dict['Take Five']),
            (users_dict['emily_w'], created_songs_dict['Clair de Lune']),
            (users_dict['alex_r'], created_songs_dict['Blinding Lights']),
            (users_dict['alex_r'], created_songs_dict['Midnight City']),
            (users_dict['marcus_v'], created_songs_dict["God's Plan"]),
            (users_dict['marcus_v'], created_songs_dict['Sicko Mode']),
            (users_dict['sophia_c'], created_songs_dict['As It Was']),
            (users_dict['sophia_c'], created_songs_dict['Bad Guy (Official Music Video)']),
        ]

        fav_count = 0
        for user_obj, song_obj in favorites_data:
            fav, created = FavoriteSong.objects.get_or_create(user=user_obj, song=song_obj)
            if created:
                fav_count += 1

        self.stdout.write(self.style.SUCCESS(f"Data seeding completed! Added {len(users_data)} users, {len(songs_data)} songs, {len(playlists_data)} playlists, and {len(favorites_data)} favorites."))
