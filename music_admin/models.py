from django.db import models

# Create your models here.
class UserRole(models.Model):
 
    role_id     = models.AutoField(primary_key=True)
    role_name   = models.CharField(max_length=100)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    deleted_at  = models.BooleanField(default=0)
    
    class Meta:
        db_table = 'role'


class User(models.Model):
    user_id         = models.AutoField(primary_key=True)
    user_name       = models.CharField(max_length=355)
    user_email      = models.CharField(max_length=255)
    user_phone      = models.CharField(max_length=255, null=True, blank=True)
    user_password   = models.CharField(max_length=255, null=True, blank=True)
    user_status     = models.BooleanField(default=0)
    user_profile_pic= models.ImageField(upload_to='profile/', blank=True, null=True, default='images/img.png')
    user_role       = models.ForeignKey(UserRole, on_delete=models.CASCADE, null=True)

    deleted_at      = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(null=True, blank=True)
    user_last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "users"

    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()


class Session(models.Model):
    session_id      = models.AutoField(primary_key=True)
    session_email   = models.EmailField()
    session_user    = models.ForeignKey(User, on_delete=models.CASCADE)
    session_token   = models.TextField()
    session_expire  = models.DateTimeField()
    session_status  = models.BooleanField(default=0)

    deleted_at      = models.DateTimeField(null=True)
    created_at      = models.DateTimeField(auto_now=True)
    updated_at      = models.DateTimeField(null=True)

    class Meta:
        db_table = "sessions"

    def update(self,*args, **kwargs):
        for name,values in kwargs.items():
            try:
                setattr(self,name,values)
            except KeyError:
                pass
        self.save()


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
    audio_file = models.FileField(upload_to='songs/')
    duration = models.DurationField()
    created_at = models.DateTimeField(auto_now_add=True)
    media_type = models.CharField(max_length=10, choices=[('audio', 'Audio'), ('video', 'Video')], null=True, blank=True)

    class Meta:
        db_table = "Songs"

    def __str__(self):
        return f"{self.title} - {self.artist}"