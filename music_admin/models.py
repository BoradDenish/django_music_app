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
    user_password   = models.CharField(max_length=255, null=True)
    sweet_word      = models.CharField(max_length=255, null=True)
    user_status     = models.BooleanField(default=0)
    user_profile_pic= models.ImageField(upload_to='profile/', blank=True, null=True, default='images/img.png')
    user_role       = models.ForeignKey(UserRole, on_delete=models.CASCADE, null=True)

    deleted_at      = models.DateTimeField(null=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(null=True)

    class meta:
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
    session_email   = models.EmailField(unique=True)
    session_user    = models.ForeignKey(User, on_delete=models.CASCADE)
    session_token   = models.TextField()

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