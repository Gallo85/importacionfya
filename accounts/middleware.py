from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from django.urls import reverse

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        logout_time = getattr(settings, 'SESSION_EXPIRE_SECONDS', 900)  # 15 minutos
        last_activity = request.session.get('last_activity')

        if last_activity:
            last_activity = datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S")
            if datetime.now() - last_activity > timedelta(seconds=logout_time):
                from django.contrib.auth import logout
                logout(request)
                return redirect('login')  # Redirigir a la página de login

        request.session['last_activity'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.get_response(request)



class RestrictIPMiddleware(MiddlewareMixin):
    ALLOWED_EMPLOYEE_IP = "45.161.118.183"  # IP permitida para empleados

    def process_request(self, request):
        login_url = reverse("login")

        # Evita que el middleware se aplique en la URL de login para evitar bucles de redirección
        if request.path == login_url:
            return None

        if not request.user.is_authenticated:
            return None

        user_ip = self.get_client_ip(request)
        user_role = getattr(request.user, 'role', None)

        if user_role == "Empleado" and user_ip != self.ALLOWED_EMPLOYEE_IP:
            messages.add_message(request, messages.ERROR, "Acceso denegado")
            return redirect(login_url)

        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip