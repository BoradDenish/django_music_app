import datetime
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from music_player.forms import (
    AdminUserCreateForm, AdminUserEditForm, PlaylistForm, SignUpForm, UserProfileForm
)
from music_player.models import FavoriteSong, Playlist, Song, User
from music_player.views import (
    activate_premium, add_song, add_to_playlist, add_user, admin_dashboard,
    admin_login, admin_logout, admin_songs, admin_toggle_premium, admin_users,
    admin_video, cancel_premium, create_playlist, delete_song, delete_user,
    delete_user_song, edit_song, edit_user, extract_youtube_id, favorites,
    get_playlists, get_user_songs_queryset, home, index, library, login_view,
    logout_view, music_library, my_uploads, parse_duration_str, playlist,
    playlist_detail, profile, record_play, remove_from_playlist, signup_view,
    toggle_favorite, trending, upgrade_premium, upload_song, video_library
)


# ---------------------------------------------------------------------------
# Base Test Setup
# ---------------------------------------------------------------------------

@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class BaseMusicTestCase(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

        # Admin User
        self.admin_user = User.objects.create_superuser(
            username='admin_boss',
            email='admin@musicapp.com',
            password='Password123!',
            user_phone='+15550000001'
        )

        # Regular Users
        self.user1 = User.objects.create_user(
            username='alice',
            email='alice@musicapp.com',
            password='Password123!',
            user_phone='+15550000002'
        )
        self.user2 = User.objects.create_user(
            username='bob',
            email='bob@musicapp.com',
            password='Password123!',
            user_phone='+15550000003'
        )

        # Public Songs
        self.song_free = Song.objects.create(
            title='Free Pop Anthem',
            artist='Pop Star',
            album='Pop Hits',
            genre='Pop',
            release_date='2024-01-01',
            duration=datetime.timedelta(minutes=3, seconds=30),
            media_type='audio',
            is_public=True,
            is_premium=False,
            play_count=100
        )
        self.song_vip = Song.objects.create(
            title='VIP Lossless Audio',
            artist='VIP Artist',
            album='VIP Suite',
            genre='Electronic',
            release_date='2024-02-01',
            duration=datetime.timedelta(minutes=4, seconds=15),
            media_type='audio',
            is_public=True,
            is_premium=True,
            play_count=50
        )
        self.video_song = Song.objects.create(
            title='Music Video Concert',
            artist='Live Performer',
            genre='Rock',
            release_date='2024-03-01',
            duration=datetime.timedelta(minutes=5, seconds=0),
            media_type='video',
            youtube_id='dQw4w9WgXcQ',
            is_public=True,
            is_premium=False,
            play_count=200
        )

    def _setup_request(self, req, user):
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(req)
        req.session.save()
        messages = FallbackStorage(req)
        setattr(req, '_messages', messages)
        req.user = user
        return req


# ---------------------------------------------------------------------------
# 1. Model Tests
# ---------------------------------------------------------------------------

class ModelTests(BaseMusicTestCase):
    def test_user_properties_free_plan(self):
        user = self.user1
        self.assertFalse(user.is_vip)
        self.assertEqual(user.uploaded_count, 0)
        self.assertEqual(user.upload_limit, 20)
        self.assertEqual(user.uploads_remaining, 20)
        self.assertEqual(user.upload_percentage, 0)
        self.assertTrue(user.can_upload())
        self.assertEqual(str(user), 'alice')
        self.assertIn('img.png', user.profile_pic_url)

    def test_user_properties_vip_plan(self):
        self.user1.is_premium = True
        self.user1.premium_expiry = timezone.now() + datetime.timedelta(days=30)
        self.user1.save()

        self.assertTrue(self.user1.is_vip)
        self.assertIsNone(self.user1.upload_limit)
        self.assertEqual(self.user1.uploads_remaining, "Unlimited")
        self.assertEqual(self.user1.upload_percentage, 100)
        self.assertTrue(self.user1.can_upload())

    def test_user_vip_expired(self):
        # When subscription is in the past, user is no longer VIP
        self.user1.is_premium = True
        self.user1.premium_expiry = timezone.now() - datetime.timedelta(days=1)
        self.user1.save()

        self.assertFalse(self.user1.is_vip)
        self.assertEqual(self.user1.upload_limit, 20)
        self.assertEqual(self.user1.uploads_remaining, 20)

    def test_user_staff_always_vip(self):
        self.assertTrue(self.admin_user.is_vip)
        self.assertIsNone(self.admin_user.upload_limit)

    def test_song_properties(self):
        self.assertEqual(str(self.song_free), "Free Pop Anthem - Pop Star")
        self.assertEqual(self.song_free.formatted_duration, "3:30")
        self.assertFalse(self.song_free.is_user_upload)
        self.assertEqual(self.song_free.audio_url, "")
        self.assertIn("default.jpg", self.song_free.cover_url)

        # Song with youtube_id gets YouTube thumbnail
        self.assertIn("dQw4w9WgXcQ", self.video_song.cover_url)

        # Formatted duration for song with None duration
        song_no_dur = Song.objects.create(title="No Dur", artist="Anon")
        self.assertEqual(song_no_dur.formatted_duration, "0:00")

    def test_playlist_model(self):
        playlist_obj = Playlist.objects.create(user=self.user1, name="My Jams")
        self.assertEqual(str(playlist_obj), "My Jams")
        self.assertEqual(playlist_obj.song_count, 0)
        playlist_obj.songs.add(self.song_free)
        self.assertEqual(playlist_obj.song_count, 1)

    def test_favorite_song_model(self):
        fav = FavoriteSong.objects.create(user=self.user1, song=self.song_free)
        self.assertEqual(str(fav), "alice - Free Pop Anthem")

        # Unique constraint test
        with self.assertRaises(Exception):
            FavoriteSong.objects.create(user=self.user1, song=self.song_free)


# ---------------------------------------------------------------------------
# 2. Form Tests
# ---------------------------------------------------------------------------

class FormTests(BaseMusicTestCase):
    def test_signup_form_valid(self):
        form = SignUpForm(data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'phone': '1234567890',
            'password1': 'secret123',
            'password2': 'secret123'
        })
        self.assertTrue(form.is_valid())

    def test_signup_form_duplicate_username(self):
        form = SignUpForm(data={
            'username': 'alice',
            'email': 'unique@example.com',
            'password1': 'secret123',
            'password2': 'secret123'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_signup_form_duplicate_email(self):
        form = SignUpForm(data={
            'username': 'newuser',
            'email': 'alice@musicapp.com',
            'password1': 'secret123',
            'password2': 'secret123'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_signup_form_mismatched_password(self):
        form = SignUpForm(data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'secret123',
            'password2': 'different123'
        })
        self.assertFalse(form.is_valid())

    def test_profile_form_duplicate_email(self):
        form = UserProfileForm(data={'email': 'bob@musicapp.com'}, instance=self.user1)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_playlist_form_empty_name(self):
        form = PlaylistForm(data={'name': '   '})
        self.assertFalse(form.is_valid())


# ---------------------------------------------------------------------------
# 3. Authentication & Public Views Tests
# ---------------------------------------------------------------------------

class AuthAndPublicViewsTests(BaseMusicTestCase):
    def test_index_anonymous(self):
        req = self.rf.get('/')
        req.user = AnonymousUser()
        resp = index(req)
        self.assertEqual(resp.status_code, 200)

    def test_index_authenticated_redirects(self):
        req = self.rf.get('/')
        req.user = self.user1
        resp = index(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('home'))

    def test_login_view_username(self):
        req = self._setup_request(self.rf.post('/login', {'email': 'alice', 'password': 'Password123!'}), AnonymousUser())
        resp = login_view(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('home'))

    def test_login_redirects_to_next_url(self):
        req = self._setup_request(self.rf.post('/login?next=/profile', {
            'email': 'alice', 'password': 'Password123!'
        }), AnonymousUser())
        resp = login_view(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/profile')

    def test_login_view_email(self):
        req = self._setup_request(self.rf.post('/login', {'email': 'alice@musicapp.com', 'password': 'Password123!'}), AnonymousUser())
        resp = login_view(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('home'))

    def test_login_view_invalid_credentials(self):
        req = self._setup_request(self.rf.post('/login', {'email': 'alice', 'password': 'WrongPassword'}), AnonymousUser())
        resp = login_view(req)
        self.assertEqual(resp.status_code, 200)

    def test_signup_view_success(self):
        req = self._setup_request(self.rf.post('/signup', {
            'username': 'charlie',
            'email': 'charlie@musicapp.com',
            'phone': '1234567890',
            'password1': 'secret123',
            'password2': 'secret123'
        }), AnonymousUser())
        resp = signup_view(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('home'))
        self.assertTrue(User.objects.filter(username='charlie').exists())

    def test_signup_view_validations(self):
        # Empty username
        req = self._setup_request(self.rf.post('/signup', {
            'username': '',
            'email': 'test@musicapp.com',
            'password1': 'secret123',
            'password2': 'secret123'
        }), AnonymousUser())
        resp = signup_view(req)
        self.assertEqual(resp.status_code, 200)

        # Duplicate username
        req2 = self._setup_request(self.rf.post('/signup', {
            'username': 'alice',
            'email': 'alice2@musicapp.com',
            'password1': 'secret123',
            'password2': 'secret123'
        }), AnonymousUser())
        resp2 = signup_view(req2)
        self.assertEqual(resp2.status_code, 200)

        # Mismatched password
        req3 = self._setup_request(self.rf.post('/signup', {
            'username': 'david',
            'email': 'david@musicapp.com',
            'password1': 'secret123',
            'password2': 'wrong123'
        }), AnonymousUser())
        resp3 = signup_view(req3)
        self.assertEqual(resp3.status_code, 200)

    def test_logout_view(self):
        req = self._setup_request(self.rf.get('/logout'), self.user1)
        resp = logout_view(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('index'))


# ---------------------------------------------------------------------------
# 4. User Core Features Tests
# ---------------------------------------------------------------------------

class UserCoreViewsTests(BaseMusicTestCase):
    def test_home_view(self):
        req = self._setup_request(self.rf.get('/home'), self.user1)
        resp = home(req)
        self.assertEqual(resp.status_code, 200)

    def test_trending_view(self):
        req = self._setup_request(self.rf.get('/trending'), self.user1)
        resp = trending(req)
        self.assertEqual(resp.status_code, 200)

    def test_library_search(self):
        req = self._setup_request(self.rf.get('/library?search=Anthem'), self.user1)
        resp = library(req)
        self.assertEqual(resp.status_code, 200)

    def test_music_library_genre_filter(self):
        req = self._setup_request(self.rf.get('/music_library?genre=Pop'), self.user1)
        resp = music_library(req)
        self.assertEqual(resp.status_code, 200)

    def test_video_library(self):
        req = self._setup_request(self.rf.get('/video_library?search=Concert'), self.user1)
        resp = video_library(req)
        self.assertEqual(resp.status_code, 200)

    def test_favorites_view(self):
        FavoriteSong.objects.create(user=self.user1, song=self.song_free)
        req = self._setup_request(self.rf.get('/favorites'), self.user1)
        resp = favorites(req)
        self.assertEqual(resp.status_code, 200)

    def test_playlist_crud(self):
        # Create playlist via POST
        req = self._setup_request(self.rf.post('/playlist', {'name': 'Summer Mix', 'description': 'Cool tracks'}), self.user1)
        resp = playlist(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('playlist'))
        pl = Playlist.objects.get(name='Summer Mix', user=self.user1)

        # View playlist detail
        req_det = self._setup_request(self.rf.get(f'/playlist/{pl.id}'), self.user1)
        resp_det = playlist_detail(req_det, playlist_id=pl.id)
        self.assertEqual(resp_det.status_code, 200)

        # Accessing another user's playlist raises 404
        req_other = self._setup_request(self.rf.get(f'/playlist/{pl.id}'), self.user2)
        with self.assertRaises(Http404):
            playlist_detail(req_other, playlist_id=pl.id)

    def test_profile_update(self):
        req = self._setup_request(self.rf.post('/profile', {
            'email': 'alice_new@musicapp.com',
            'phone': '+1999888777'
        }), self.user1)
        resp = profile(req)
        self.assertEqual(resp.status_code, 302)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.email, 'alice_new@musicapp.com')
        self.assertEqual(self.user1.user_phone, '+1999888777')

    def test_profile_update_duplicate_email_rejected(self):
        # Alice tries to take Bob's email
        req = self._setup_request(self.rf.post('/profile', {
            'email': 'bob@musicapp.com',
            'phone': '+1999888777'
        }), self.user1)
        resp = profile(req)
        self.assertEqual(resp.status_code, 302)
        self.user1.refresh_from_db()
        self.assertNotEqual(self.user1.email, 'bob@musicapp.com')


# ---------------------------------------------------------------------------
# 5. Uploads Quota & Privacy Tests
# ---------------------------------------------------------------------------

class UploadsAndQuotaTests(BaseMusicTestCase):
    def test_song_privacy_isolation(self):
        user1_song = Song.objects.create(
            title="Secret Track", artist="Alice", is_public=False, uploaded_by=self.user1
        )
        # Alice can see it
        alice_songs = get_user_songs_queryset(self.user1)
        self.assertIn(user1_song, alice_songs)

        # Bob CANNOT see Alice's private song
        bob_songs = get_user_songs_queryset(self.user2)
        self.assertNotIn(user1_song, bob_songs)

    def test_20_song_quota_limit(self):
        for i in range(20):
            Song.objects.create(
                title=f"Track {i}", artist="Alice", is_public=False, uploaded_by=self.user1
            )
        self.assertEqual(self.user1.uploaded_count, 20)
        self.assertFalse(self.user1.can_upload())

        # Attempting upload when quota is full redirects to premium
        req = self._setup_request(self.rf.get('/upload'), self.user1)
        resp = upload_song(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('upgrade_premium'))

    def test_delete_user_song_frees_quota(self):
        song = Song.objects.create(
            title="Temp Track", artist="Alice", is_public=False, uploaded_by=self.user1
        )
        self.assertEqual(self.user1.uploaded_count, 1)

        req = self._setup_request(self.rf.post(f'/my_uploads/delete/{song.id}'), self.user1)
        resp = delete_user_song(req, song_id=song.id)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.user1.uploaded_count, 0)

    def test_cannot_delete_other_user_song(self):
        bobs_song = Song.objects.create(
            title="Bob Song", artist="Bob", is_public=False, uploaded_by=self.user2
        )
        req = self._setup_request(self.rf.post(f'/my_uploads/delete/{bobs_song.id}'), self.user1)
        with self.assertRaises(Http404):
            delete_user_song(req, song_id=bobs_song.id)

    @patch('music_player.views.get_youtube_info')
    def test_upload_song_via_youtube_import(self, mock_info):
        mock_info.return_value = {
            'title': 'Imported Hit',
            'artist': 'YouTube Star',
            'album': 'Single',
            'duration': datetime.timedelta(minutes=3),
            'thumbnail': None,
            'release_date': '2024-01-01'
        }
        req = self._setup_request(self.rf.post('/upload', {
            'upload_type': 'youtube',
            'content_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'content_type': 'audio'
        }), self.user1)
        resp = upload_song(req)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Song.objects.filter(title='Imported Hit', uploaded_by=self.user1).exists())


# ---------------------------------------------------------------------------
# 6. Premium VIP Subscription Tests
# ---------------------------------------------------------------------------

class PremiumMembershipTests(BaseMusicTestCase):
    def test_upgrade_premium_page(self):
        req = self._setup_request(self.rf.get('/premium'), self.user1)
        resp = upgrade_premium(req)
        self.assertEqual(resp.status_code, 200)

    def test_activate_and_cancel_premium(self):
        # Activate monthly
        req = self._setup_request(self.rf.post('/premium/activate', {'plan': 'monthly'}), self.user1)
        resp = activate_premium(req)
        self.assertEqual(resp.status_code, 302)
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.is_premium)
        self.assertTrue(self.user1.is_vip)

        # Cancel
        req_cancel = self._setup_request(self.rf.post('/premium/cancel'), self.user1)
        resp_cancel = cancel_premium(req_cancel)
        self.assertEqual(resp_cancel.status_code, 302)
        self.user1.refresh_from_db()
        self.assertFalse(self.user1.is_premium)
        self.assertFalse(self.user1.is_vip)


# ---------------------------------------------------------------------------
# 7. AJAX Endpoints Tests
# ---------------------------------------------------------------------------

class AjaxEndpointsTests(BaseMusicTestCase):
    def test_toggle_favorite(self):
        # Favorite
        req = self._setup_request(self.rf.post('/toggle-favorite', {'song_id': self.song_free.id}), self.user1)
        resp = toggle_favorite(req)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(FavoriteSong.objects.filter(user=self.user1, song=self.song_free).exists())

        # Unfavorite
        req2 = self._setup_request(self.rf.post('/toggle-favorite', {'song_id': self.song_free.id}), self.user1)
        resp2 = toggle_favorite(req2)
        self.assertEqual(resp2.status_code, 200)
        self.assertFalse(FavoriteSong.objects.filter(user=self.user1, song=self.song_free).exists())

    def test_playlist_ajax_endpoints(self):
        pl = Playlist.objects.create(user=self.user1, name="My Mix")

        # Get playlists
        req_get = self._setup_request(self.rf.get('/get-playlists'), self.user1)
        resp_get = get_playlists(req_get)
        self.assertEqual(resp_get.status_code, 200)
        self.assertIn("My Mix", resp_get.content.decode())

        # Add to playlist
        req_add = self._setup_request(self.rf.post('/add-to-playlist', {
            'song_id': self.song_free.id,
            'playlist_id': pl.id
        }), self.user1)
        resp_add = add_to_playlist(req_add)
        self.assertEqual(resp_add.status_code, 200)
        self.assertIn(self.song_free, pl.songs.all())

        # Add duplicate
        resp_dup = add_to_playlist(req_add)
        self.assertEqual(resp_dup.status_code, 200)
        self.assertIn("already_in", resp_dup.content.decode())

        # Remove from playlist
        req_rem = self._setup_request(self.rf.post('/remove-from-playlist', {
            'song_id': self.song_free.id,
            'playlist_id': pl.id
        }), self.user1)
        resp_rem = remove_from_playlist(req_rem)
        self.assertEqual(resp_rem.status_code, 200)
        self.assertNotIn(self.song_free, pl.songs.all())

    def test_create_playlist_ajax(self):
        req = self._setup_request(self.rf.post('/create-playlist', {'name': 'Ajax Playlist'}), self.user1)
        resp = create_playlist(req)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Playlist.objects.filter(name='Ajax Playlist', user=self.user1).exists())

        # Empty name fails
        req_empty = self._setup_request(self.rf.post('/create-playlist', {'name': ''}), self.user1)
        resp_empty = create_playlist(req_empty)
        self.assertEqual(resp_empty.status_code, 400)

    def test_record_play(self):
        self.assertEqual(self.song_free.play_count, 100)
        req = self._setup_request(self.rf.post('/record-play', {'song_id': self.song_free.id}), self.user1)
        resp = record_play(req)
        self.assertEqual(resp.status_code, 200)
        self.song_free.refresh_from_db()
        self.assertEqual(self.song_free.play_count, 101)


# ---------------------------------------------------------------------------
# 8. Admin Console & Management Tests
# ---------------------------------------------------------------------------

class AdminConsoleTests(BaseMusicTestCase):
    def test_regular_user_blocked_from_admin(self):
        req = self._setup_request(self.rf.get('/a/dashboard'), self.user1)
        resp = admin_dashboard(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/a/login')

    def test_admin_dashboard_metrics(self):
        req = self._setup_request(self.rf.get('/a/dashboard'), self.admin_user)
        resp = admin_dashboard(req)
        self.assertEqual(resp.status_code, 200)

    def test_admin_login_success(self):
        req = self._setup_request(self.rf.post('/a/login', {
            'email': 'admin_boss', 'password': 'Password123!'
        }), AnonymousUser())
        resp = admin_login(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('admin_dashboard'))

    def test_admin_login_redirects_to_next_url(self):
        req = self._setup_request(self.rf.post('/a/login?next=/a/users', {
            'email': 'admin_boss', 'password': 'Password123!'
        }), AnonymousUser())
        resp = admin_login(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/a/users')

    def test_admin_login_rejects_regular_user(self):
        req = self._setup_request(self.rf.post('/a/login', {
            'email': 'alice', 'password': 'Password123!'
        }), AnonymousUser())
        resp = admin_login(req)
        self.assertEqual(resp.status_code, 200)

    def test_admin_logout(self):
        req = self._setup_request(self.rf.get('/a/logout'), self.admin_user)
        resp = admin_logout(req)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('admin_login'))

    def test_admin_songs_list(self):
        req = self._setup_request(self.rf.get('/a/songs?filter=public'), self.admin_user)
        resp = admin_songs(req)
        self.assertEqual(resp.status_code, 200)

    @patch('music_player.views.get_youtube_info')
    @patch('music_player.views.download_media')
    def test_admin_add_song_with_youtube(self, mock_media, mock_info):
        mock_info.return_value = {
            'title': 'Admin Added Track',
            'artist': 'Super Artist',
            'album': 'Pop Hits',
            'duration': datetime.timedelta(minutes=3),
            'thumbnail': None,
            'release_date': '2024-01-01'
        }
        mock_media.return_value = 'songs/mock.mp3'
        req = self._setup_request(self.rf.post('/a/songs/add', {
            'title': 'Admin Added Track',
            'artist': 'Super Artist',
            'genre': 'Pop',
            'media_type': 'audio',
            'youtube_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'is_public': 'on',
            'is_premium': 'on'
        }), self.admin_user)
        resp = add_song(req)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Song.objects.filter(title='Admin Added Track', is_premium=True).exists())

    def test_admin_add_song_requires_file_or_yt(self):
        # Neither file nor youtube link provided
        req = self._setup_request(self.rf.post('/a/songs/add', {
            'title': 'Empty Track',
            'artist': 'Nobody'
        }), self.admin_user)
        resp = add_song(req)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Song.objects.filter(title='Empty Track').exists())

    def test_admin_edit_song(self):
        req = self._setup_request(self.rf.post(f'/a/songs/edit/{self.song_free.id}', {
            'title': 'Updated Title',
            'artist': 'Updated Artist',
            'genre': 'Jazz',
            'is_public': 'on',
            'is_premium': 'on'
        }), self.admin_user)
        resp = edit_song(req, song_id=self.song_free.id)
        self.assertEqual(resp.status_code, 302)
        self.song_free.refresh_from_db()
        self.assertEqual(self.song_free.title, 'Updated Title')
        self.assertTrue(self.song_free.is_premium)

    def test_admin_delete_song(self):
        req = self._setup_request(self.rf.post(f'/a/songs/delete/{self.song_free.id}'), self.admin_user)
        resp = delete_song(req, song_id=self.song_free.id)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Song.objects.filter(id=self.song_free.id).exists())

    def test_admin_users_list(self):
        req = self._setup_request(self.rf.get('/a/users?search=alice'), self.admin_user)
        resp = admin_users(req)
        self.assertEqual(resp.status_code, 200)

    def test_admin_add_user(self):
        req = self._setup_request(self.rf.post('/a/users/add', {
            'username': 'newstaff',
            'email': 'staff@musicapp.com',
            'password': 'password123',
            'is_staff': 'on',
            'is_premium': 'on'
        }), self.admin_user)
        resp = add_user(req)
        self.assertEqual(resp.status_code, 302)
        u = User.objects.get(username='newstaff')
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_premium)

    def test_admin_edit_user(self):
        req = self._setup_request(self.rf.post(f'/a/users/edit/{self.user1.id}', {
            'username': 'alice_edited',
            'email': 'alice_new@musicapp.com',
            'user_phone': '9999999999',
            'is_premium': 'on'
        }), self.admin_user)
        resp = edit_user(req, user_id=self.user1.id)
        self.assertEqual(resp.status_code, 302)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, 'alice_edited')
        self.assertTrue(self.user1.is_premium)

    def test_admin_edit_user_duplicate_username_fails(self):
        # Try to rename alice to bob's username
        req = self._setup_request(self.rf.post(f'/a/users/edit/{self.user1.id}', {
            'username': 'bob',
            'email': 'alice@musicapp.com'
        }), self.admin_user)
        resp = edit_user(req, user_id=self.user1.id)
        self.assertEqual(resp.status_code, 200)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, 'alice')

    def test_admin_toggle_premium(self):
        self.assertFalse(self.user2.is_premium)
        req = self._setup_request(self.rf.post(f'/a/users/toggle-premium/{self.user2.id}'), self.admin_user)
        resp = admin_toggle_premium(req, user_id=self.user2.id)
        self.assertEqual(resp.status_code, 302)
        self.user2.refresh_from_db()
        self.assertTrue(self.user2.is_premium)

    def test_admin_cannot_delete_own_account(self):
        req = self._setup_request(self.rf.post(f'/a/users/delete/{self.admin_user.id}'), self.admin_user)
        resp = delete_user(req, user_id=self.admin_user.id)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(id=self.admin_user.id).exists())

    def test_admin_can_delete_other_user(self):
        req = self._setup_request(self.rf.post(f'/a/users/delete/{self.user2.id}'), self.admin_user)
        resp = delete_user(req, user_id=self.user2.id)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(User.objects.filter(id=self.user2.id).exists())

    def test_admin_video_view(self):
        req = self._setup_request(self.rf.get('/a/videos'), self.admin_user)
        resp = admin_video(req)
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# 9. Utilities & Parsers Tests
# ---------------------------------------------------------------------------

class UtilitiesTests(BaseMusicTestCase):
    def test_extract_youtube_id(self):
        self.assertEqual(extract_youtube_id('https://www.youtube.com/watch?v=dQw4w9WgXcQ'), 'dQw4w9WgXcQ')
        self.assertEqual(extract_youtube_id('https://youtu.be/dQw4w9WgXcQ'), 'dQw4w9WgXcQ')
        self.assertEqual(extract_youtube_id('https://music.youtube.com/watch?v=dQw4w9WgXcQ&si=123'), 'dQw4w9WgXcQ')
        self.assertEqual(extract_youtube_id('https://www.youtube.com/shorts/dQw4w9WgXcQ'), 'dQw4w9WgXcQ')
        self.assertEqual(extract_youtube_id('https://www.youtube.com/embed/dQw4w9WgXcQ'), 'dQw4w9WgXcQ')
        self.assertEqual(extract_youtube_id('https://m.youtube.com/watch?v=dQw4w9WgXcQ'), 'dQw4w9WgXcQ')

        # Invalid URLs
        self.assertIsNone(extract_youtube_id('https://example.com/watch?v=123'))
        self.assertIsNone(extract_youtube_id(''))
        self.assertIsNone(extract_youtube_id(None))

    def test_parse_duration_str(self):
        self.assertEqual(parse_duration_str('01:30:00'), datetime.timedelta(hours=1, minutes=30))
        self.assertEqual(parse_duration_str('03:45'), datetime.timedelta(minutes=3, seconds=45))
        self.assertEqual(parse_duration_str('45'), datetime.timedelta(seconds=45))
        self.assertIsNone(parse_duration_str('invalid'))
        self.assertIsNone(parse_duration_str(''))
        self.assertIsNone(parse_duration_str(None))
