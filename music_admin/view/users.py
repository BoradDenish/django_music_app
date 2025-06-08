from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.templatetags.static import static
from music_admin.models import User, UserRole
import logging
import os

# Logging setup for users.py
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log')
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger('users_logger')
handler = logging.FileHandler(os.path.join(LOG_DIR, 'users.log'))
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def admin_users(request):
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)

    users_queryset = User.objects.filter(user_role=2, deleted_at__isnull=True).order_by('user_id')
    if search_query:
        users_queryset = users_queryset.filter(user_name__icontains=search_query)

    paginator = Paginator(users_queryset, 10)

    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)


    for user in users_page:
        if user.user_profile_pic:
            user.user_profile_url = request.build_absolute_uri(user.user_profile_pic.url)
            print(request.build_absolute_uri(user.user_profile_pic.url))
        else:
            user.user_profile_url = request.build_absolute_uri(static("images/default_user.jpg"))

    context = {
        "users": users_page,
        "search_query": search_query,
    }
    return render(request, "admin/users/admin_users.html", context)


def add_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        user_img = request.FILES.get("user_img")

        if not username or not email:
            messages.error(request, "Username and Email are required.")
            return render(request, "admin/users/user_add.html")

        try:
            new_user = User(
                user_name=username,
                user_email=email,
                user_profile_pic=user_img,
                user_status=1,  # Active
                user_role=UserRole.objects.get(role_id=2)
            )
            new_user.full_clean()
            new_user.save()
            messages.success(request, "User added successfully.")
            logger.info(f"User added: {username} ({email})")
            return redirect("admin_users")
        except ValidationError as e:
            messages.error(request, f"Validation error: {e}")
            logger.warning(f"Validation error when adding user {username}: {e}")
        except UserRole.DoesNotExist:
            messages.error(request, "User role not found.")
            logger.error(f"User role not found when adding user {username}")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
            logger.error(f"Unexpected error when adding user {username}: {e}")

    return render(request, "admin/users/user_add.html")


def edit_user(request, user_id):
    user = get_object_or_404(User, user_id=user_id)

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        profile_picture = request.FILES.get("profile_picture")

        if not username or not email:
            messages.error(request, "Username and Email are required.")
            return render(request, "admin/users/user_edit.html", {"user": user})

        user.user_name = username
        user.user_email = email
        if profile_picture:
            user.user_profile_pic = profile_picture

        try:
            user.full_clean()
            user.save()
            messages.success(request, "User updated successfully.")
            logger.info(f"User updated: {username} ({email})")
            return redirect("admin_users")
        except ValidationError as e:
            messages.error(request, f"Validation error: {e}")
            logger.warning(f"Validation error when updating user {username}: {e}")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
            logger.error(f"Unexpected error when updating user {username}: {e}")

    return render(request, "admin/users/user_edit.html", {"user": user})



def delete_user(request, id):
    if request.method == "POST":
        user = get_object_or_404(User, user_id=id)
        user.deleted_at = timezone.now()
        user.save()
        messages.success(request, "User deleted successfully.")
        logger.info(f"User deleted: {user.user_name} ({user.user_email})")
        return redirect("admin_users")
    else:
        messages.error(request, "Invalid request method.")
        logger.warning(f"Invalid request method for deleting user ID {id}")
        return redirect("admin_users")
