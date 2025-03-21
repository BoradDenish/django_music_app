from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from music_admin.models import Song, User

# Create your views here.

def index(request):
    return JsonResponse({"HELLO": "MESSAGE"})



def admin_login(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:  # Ensures only admins can log in
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid credentials or not an admin.")

    return render(request, 'admin/auth/admin_login.html')

def admin_logout(request):
    logout(request)
    return redirect('admin_login')



def admin_dashboard(request):
    context = {
        "total_users": User.objects.count(),
        # "total_songs": Song.objects.count(),
        "total_playlists": 10,  # Example value
    }
    return render(request, "admin/admin_dashboard.html", context)

def admin_songs(request):
    songs = Song.objects.all()
    return render(request, "admin_songs.html", {"songs": songs})

def admin_users(request):
    users = User.objects.all()
    return render(request, "admin_users.html", {"users": users})