def site_config(request):
    """Injecte la config globale du site dans tous les templates via {{ site_config.xxx }}."""
    try:
        from apps.core.models import SiteConfiguration
        config = SiteConfiguration.get_solo()
    except Exception:
        config = None
    return {'site_config': config}
