from django.shortcuts import render

# Paths that always bypass maintenance mode
_BYPASS_PREFIXES = (
    '/admin/',
    '/health/',
    '/maintenance/',
    '/static/',
    '/media/',
    '/api/schema/',
    '/api/docs/',
    '/api/redoc/',
)


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        # Always let through bypass paths
        if any(path.startswith(p) for p in _BYPASS_PREFIXES):
            return self.get_response(request)

        # Admins see the site normally
        if request.session.get('user_role') == 'admin':
            return self.get_response(request)

        # Lazy import to avoid app-registry issues at startup
        from apps.core.models import SiteConfiguration
        try:
            config = SiteConfiguration.get_solo()
        except Exception:
            return self.get_response(request)

        if config.maintenance_mode:
            return render(
                request,
                'maintenance.html',
                {'config': config},
                status=503,
            )

        return self.get_response(request)
