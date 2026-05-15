import os
from urllib.parse import urlparse
from .base import *

DEBUG = False

# --- ALLOWED_HOSTS — auto-détection Railway + domaine custom ---
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'healthcheck.railway.app']

# Railway injecte RAILWAY_PUBLIC_DOMAIN automatiquement (ex: mon-app.up.railway.app)
_railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '')
if _railway_domain:
    ALLOWED_HOSTS.append(_railway_domain)

# SITE_URL = source de vérité pour le domaine custom (ex: https://ecocycle.ht)
_site_url = os.environ.get('SITE_URL', '')
if _site_url:
    _host = urlparse(_site_url).hostname
    if _host and _host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_host)

# Hosts supplémentaires via variable Railway ALLOWED_HOSTS (ex: "ecocycle.ht,www.ecocycle.ht")
_extra_hosts = os.environ.get('ALLOWED_HOSTS', '')
if _extra_hosts:
    ALLOWED_HOSTS += [h.strip() for h in _extra_hosts.split(',') if h.strip()]

# --- CSRF TRUSTED ORIGINS ---
CSRF_TRUSTED_ORIGINS = ['http://localhost', 'http://127.0.0.1']
if _railway_domain:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_railway_domain}')
if _site_url and _site_url not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(_site_url)
_extra_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if _extra_origins:
    CSRF_TRUSTED_ORIGINS += [o.strip() for o in _extra_origins.split(',') if o.strip()]

# --- CORS ---
_cors_env = os.environ.get('CORS_ALLOWED_ORIGINS', '')
CORS_ALLOWED_ORIGINS = (
    [o.strip() for o in _cors_env.split(',') if o.strip()]
    if _cors_env else []
)

# --- SÉCURITÉ PROXY (Railway termine HTTPS au niveau load balancer) ---
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False   # Railway gère la redirection HTTP→HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
