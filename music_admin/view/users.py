from django.shortcuts import redirect, render
from django.core.exceptions import ValidationError
from music_admin.models import User, UserRole
from django.contrib import messages


def admin_users(request):
    users = []
    all_user = User.objects.filter(user_role=2).all()
    for user in all_user:
        user_data = {
            "id": user.user_id,
            "username": user.user_name,
            "email": user.user_email,
            "profile_pic": user.user_profile_pic.url if user.user_profile_pic else None,
            "status": user.user_status,
            "role": user.user_role.role_name if user.user_role else None
        }
        users.append(user_data)
    # users = [
    #     {"id": 1, "username": "Denish", "email": "denish@gmail.com"},
    #     {"id": 2, "username": "Denish1", "email": "denish1@gmail.com"},
    #     {"id": 3, "username": "Denish2", "email": "denish2@gmail.com"},
    #     {"id": 4, "username": "Denish3", "email": "denish3@gmail.com"}
    # ]
    return render(request, "admin/users/admin_users.html", {"users": users})

def add_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        user_img = request.FILES.get("user_img")

        # Basic validation (you can add more as needed)
        if not username or not email:
            messages.error(request, "Username and Email are required.")
            return render(request, "admin/users/user_add.html")

        try:
            new_user = User(
                user_name=username,
                user_email=email,
                user_profile_pic=user_img,
                user_status=1,  # Assuming 1 means active
                user_role=UserRole.objects.get(role_id=2)     # Assuming 2 is a predefined role ID
            )
            new_user.full_clean()  # Optional: validate model fields
            new_user.save()
            messages.success(request, "User added successfully.")
            return redirect("admin_users")  # Redirect to user listing page
        except ValidationError as e:
            messages.error(request, f"Validation error: {e}")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

    return render(request, "admin/users/user_add.html")

def edit_user(request):
    # user = User.objects.get(id=id)
    if request.method == "POST":
        # Handle form submission and user update
        username = request.POST.get("username")
        email = request.POST.get("email")
        # Add logic to update the user in the database
        # messages.success(request, "User updated successfully.")
        return render(request, "admin/users/admin_users.html")
    return render(request, "admin/users/user_edit.html", {"id": 1})

def delete_user(request, id):
    # user = User.objects.get(id=id)
    # user.delete()
    # return redirect('admin_users')
    return render(request, "admin/users/admin_users.html")

