from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from django.contrib.sessions.models import Session
import json

EXCLUDED_PATHS = ["/", "/a/login", "/a/users", "/a/songs", "/a/dashboard", "/signup", "/login", "/dashboard","/a/home", "/forgot-pass", "/favicon.ico"]

class TokenAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path in EXCLUDED_PATHS:
            return None  # Allow access to these endpoints without token check

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JsonResponse({"error": "Authorization token missing"}, status=401)

        token = auth_header.split(" ")[-1]  # Expecting 'Bearer <token>' format
        
        try:
            session = Session.objects.get(session_key=token)
            session_data = session.get_decoded()
            expiry_date = session.expire_date
            
            if expiry_date < now():
                return JsonResponse({"error": "Token expired"}, status=401)
        except Session.DoesNotExist:
            return JsonResponse({"error": "Invalid token"}, status=401)

        return None  # Continue processing if token is valid
