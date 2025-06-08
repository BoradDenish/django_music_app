from datetime import datetime, timedelta
import secrets
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from music_admin.models import Session, User
import logging
import os

# Logging setup for authentication.py
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log')
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger('authentication_logger')
handler = logging.FileHandler(os.path.join(LOG_DIR, 'authentication.log'))
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

def admin_login(request):
    if request.method == "POST":
        useremail = request.POST.get("email")  # Fix request.POST
        password  = request.POST.get("password")

        # Validate email input before querying the database
        if not useremail:
            return JsonResponse({"status": 500, "message": "Please enter an email address!"})
        
        if not password:
            return JsonResponse({"status": 500, "message": "Please enter a password!"})

        # Fetch user record safely
        user = User.objects.exclude(user_status=0).exclude(user_role=2).filter(user_email=useremail).first()

        if not user:
            return JsonResponse({"status": 500, "message": "Email does not exist!"})

        # Validate password
        if not check_password(password, user.user_password):
            return JsonResponse({"status": 500, "message": "Invalid password! Please try again."})

        # Generate session token
        session_token = secrets.token_hex()

        # Store session token securely
        request.session["admin_session"] = {
            "session_token": session_token,
            "session_name": "admin_session",
        }
        request.session["user_profile"] = user.user_profile_pic.url if user.user_profile_pic else None

        # Set session expiry
        exp_time = timezone.now() + timedelta(days=1)

        # Store session in the database
        session_data = Session(
            session_user=user,
            session_email=useremail,
            session_token=session_token,
            session_expire=exp_time,
            session_status=1,
            created_at=datetime.now(),
        )
        session_data.save()

        # Redirect to dashboard after successful login
        return redirect("admin_dashboard")

    return render(request, "admin/auth/admin_login.html")


def admin_logout(request):
    print("Logout called", request.session)
    # Clear session data
    request.session.flush()

    # Redirect to login page
    return redirect("admin_login")  # Ensure 'admin_login' is the correct URL name

