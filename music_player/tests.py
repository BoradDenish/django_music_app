from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from music_player.models import User, Song, Playlist, FavoriteSong
from music_player.views import (
    extract_youtube_id, get_user_songs_queryset,
    home, music_library, my_uploads, upload_song,
    upgrade_premium, activate_premium, cancel_premium,
    toggle_favorite, add_to_playlist, admin_dashboard,
    admin_toggle_premium
)


class MusicSystemTestCase(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

        # Create Admin User
        self.admin_user = User.objects.create_superuser(
            username='admin_test', email='admin@test.com', password='password123'
        )

        # Create Regular Users
        self.user1 = User.objects.create_user(
            username='user1', email='user1@test.com', password='password123'
        )
        self.user2 = User.objects.create_user(
            username='user2', email='user2@test.com', password='password123'
        )

        # Create Public Songs (Admin / System)
        self.public_song_free = Song.objects.create(
            title='Public Free Track', artist='Public Artist', genre='Pop',
            release_date='2024-01-01', is_public=True, is_premium=False
        )
        self.public_song_vip = Song.objects.create(
            title='Public VIP Exclusive Track', artist='VIP Artist', genre='Electronic',
            release_date='2024-01-01', is_public=True, is_premium=True
        )

    def _setup_request(self, req, user):
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(req)
        req.session.save()
        messages = FallbackStorage(req)
        setattr(req, '_messages', messages)
        req.user = user
        return req

    def test_youtube_id_extractor(self):
        self.assertEqual(extract_youtube_id('https://www.youtube.com/watch?v=dQw4w9WgXcQ'), 'dQw4w9WgXcQ')
        self.assertEqual(extract_youtube_id('https://youtu.be/dQw4w9WgXcQ'), 'dQw4w9WgXcQ')
        self.assertEqual(extract_youtube_id('https://music.youtube.com/watch?v=dQw4w9WgXcQ&si=123'), 'dQw4w9WgXcQ')
        self.assertEqual(extract_youtube_id('https://www.youtube.com/shorts/dQw4w9WgXcQ'), 'dQw4w9WgXcQ')

    def test_song_privacy_isolation(self):
        # User 1 uploads a private song
        user1_song = Song.objects.create(
            title="User 1 Secret Song", artist="User 1", genre="Rock",
            release_date="2024-01-01", uploaded_by=self.user1, is_public=False
        )

        # User 1 accessible songs should include public songs + User 1's song
        user1_songs = get_user_songs_queryset(self.user1)
        self.assertIn(user1_song, user1_songs)
        self.assertIn(self.public_song_free, user1_songs)

        # User 2 accessible songs must NOT include User 1's private song
        user2_songs = get_user_songs_queryset(self.user2)
        self.assertNotIn(user1_song, user2_songs)
        self.assertIn(self.public_song_free, user2_songs)

    def test_user_20_song_upload_quota(self):
        # Regular user initially has 20 slots
        self.assertEqual(self.user1.uploaded_count, 0)
        self.assertTrue(self.user1.can_upload())
        self.assertEqual(self.user1.upload_limit, 20)
        self.assertEqual(self.user1.uploads_remaining, 20)

        # Create 20 songs for User 1
        for i in range(20):
            Song.objects.create(
                title=f"User Song {i+1}", artist="User 1", genre="Pop",
                release_date="2024-01-01", uploaded_by=self.user1, is_public=False
            )

        self.assertEqual(self.user1.uploaded_count, 20)
        self.assertEqual(self.user1.uploads_remaining, 0)
        self.assertFalse(self.user1.can_upload())

        # Attempting upload view when quota is full should redirect to upgrade_premium
        req = self._setup_request(self.rf.get('/upload'), self.user1)
        resp = upload_song(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/premium')

    def test_vip_unlimited_uploads(self):
        # User 1 has 20 songs
        for i in range(20):
            Song.objects.create(
                title=f"User Song {i+1}", artist="User 1", genre="Pop",
                release_date="2024-01-01", uploaded_by=self.user1, is_public=False
            )

        self.assertFalse(self.user1.can_upload())

        # Upgrade User 1 to VIP
        req = self._setup_request(self.rf.post('/premium/activate', {'plan': 'annual'}), self.user1)
        resp = activate_premium(req)
        self.assertEqual(resp.status_code, 302)
        self.user1.refresh_from_db()

        self.assertTrue(self.user1.is_premium)
        self.assertTrue(self.user1.is_vip)
        self.assertTrue(self.user1.can_upload())
        self.assertEqual(self.user1.uploads_remaining, "Unlimited")

    def test_admin_portal_permissions(self):
        # Regular user cannot access admin console
        req = self._setup_request(self.rf.get('/a/dashboard'), self.user1)
        resp = admin_dashboard(req)
        self.assertEqual(resp.status_code, 302)

        # Admin user can access admin console
        req_admin = self._setup_request(self.rf.get('/a/dashboard'), self.admin_user)
        resp_admin = admin_dashboard(req_admin)
        self.assertEqual(resp_admin.status_code, 200)

        # Admin can toggle user VIP status
        self.assertFalse(self.user2.is_premium)
        req_toggle = self._setup_request(self.rf.post(f'/a/users/toggle-premium/{self.user2.id}'), self.admin_user)
        resp_toggle = admin_toggle_premium(req_toggle, user_id=self.user2.id)
        self.assertEqual(resp_toggle.status_code, 302)
        self.user2.refresh_from_db()
        self.assertTrue(self.user2.is_premium)

    def test_ajax_favorites_and_playlists(self):
        # Toggle Favorite
        req_fav = self._setup_request(self.rf.post('/toggle-favorite', {'song_id': self.public_song_free.id}), self.user1)
        resp_fav = toggle_favorite(req_fav)
        self.assertEqual(resp_fav.status_code, 200)
        self.assertTrue(FavoriteSong.objects.filter(user=self.user1, song=self.public_song_free).exists())

        # Create Playlist
        playlist = Playlist.objects.create(user=self.user1, name="My Jam")
        req_pl = self._setup_request(self.rf.post('/add-to-playlist', {
            'song_id': self.public_song_free.id,
            'playlist_id': playlist.id
        }), self.user1)
        resp_pl = add_to_playlist(req_pl)
        self.assertEqual(resp_pl.status_code, 200)
        self.assertIn(self.public_song_free, playlist.songs.all())

    def test_record_play_increments_count(self):
        from music_player.views import record_play
        self.assertEqual(self.public_song_free.play_count, 0)

        req = self._setup_request(self.rf.post('/record-play', {'song_id': self.public_song_free.id}), self.user1)
        resp = record_play(req)
        self.assertEqual(resp.status_code, 200)

        self.public_song_free.refresh_from_db()
        self.assertEqual(self.public_song_free.play_count, 1)

    def test_url_fallbacks_and_profile_pic(self):
        # User without profile picture gets default avatar
        self.assertIn('img.png', self.user1.profile_pic_url)

        # Song with youtube_id gets YouTube thumbnail fallback if no cover image
        song_yt = Song.objects.create(
            title='YT Track', artist='YT Artist', genre='Pop',
            release_date='2024-01-01', youtube_id='test12345'
        )
        self.assertIn('test12345', song_yt.cover_url)

        # Song without audio_file returns empty string for audio_url
        self.assertEqual(song_yt.audio_url, "")

    def test_playlist_remove(self):
        from music_player.views import remove_from_playlist
        playlist = Playlist.objects.create(user=self.user1, name="Temp Playlist")
        playlist.songs.add(self.public_song_free)
        self.assertIn(self.public_song_free, playlist.songs.all())

        req = self._setup_request(self.rf.post('/remove-from-playlist', {
            'song_id': self.public_song_free.id,
            'playlist_id': playlist.id
        }), self.user1)
        resp = remove_from_playlist(req)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(self.public_song_free, playlist.songs.all())

