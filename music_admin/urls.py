from django.urls import path
from music_admin.views import index

urlpatterns = [
    path("", index, name="index")
]