from django.db import models

# Create your models here.
class User(models.Model):
    user_id     = models.AutoField(primary_key=True)
    user_name   = models.CharField(max_length=355)
    user_email  = models.CharField(max_length=255)
    user_password = models.CharField(max_length=255, null=True)
    sweet_word  = models.CharField(max_length=255, null=True)
    user_status = models.BooleanField(default=0)
    deleted_at  = models.DateTimeField(null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(null=True)

    class meta:
        db_table = "users"


class Session(models.Model):
    session_id      = models.AutoField(primary_key=True)
    session_email   = models.EmailField(unique=True)
    session_user    = models.ForeignKey(User, on_delete=models.CASCADE)
    session_token   = models.TextField()
    deleted_at      = models.DateTimeField(null=True)
    created_at      = models.DateTimeField(auto_now=True)
    updated_at      = models.DateTimeField(null=True)

    class Meta:
        db_table = "sessions"