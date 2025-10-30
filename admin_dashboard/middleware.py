from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from .models import AdminActivityLog

User = get_user_model()

class AdminActivityMiddleware(MiddlewareMixin):
    """Middleware to log admin activities"""
    
    def process_request(self, request):
        # Store the IP address in the request for admin activity logging
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.role == User.Roles.ADMIN:
                # Get client IP address
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                request.admin_ip = ip
        
        return None