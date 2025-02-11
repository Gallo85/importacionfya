from django.http import HttpResponseForbidden
from functools import wraps

def role_required(required_roles, message=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'role'):
                return HttpResponseForbidden(message or "Tu usuario no tiene un rol asignado.")
            if request.user.role not in required_roles:
                return HttpResponseForbidden(message or "No tienes permiso para acceder a esta página.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
