from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import user_login, user_logout
from django.contrib.auth.decorators import user_passes_test

# Función para verificar si el usuario es Gerente
def is_gerente(user):
    return user.is_authenticated and user.groups.filter(name='Gerente').exists()

# Restringir acceso al panel de administración solo a Gerentes
admin.site.login = user_passes_test(is_gerente)(admin.site.login)

urlpatterns = [
    path('admin/', admin.site.urls),  # Solo Gerentes pueden acceder al /admin/
    path("productos/", include("productos.urls")),  # URLs de la app productos
    path('accounts/', include('accounts.urls')),  # URLs de la app accounts
    path('login/', user_login, name='login'),  # Vista del login
    path('logout/', user_logout, name='logout'),  # Vista del logout
    path('', user_login, name='home'),  # Página inicial redirigida al login
    path('facturacion/', include(('facturacion.urls', 'facturacion'))),  # URLs de la app facturación
    path('core/', include('core.urls')),  # URLs de la app core (dashboards, etc.)
    path('divisas/', include('divisas.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
