from django.conf import settings


def get_site_base_url(request):
    configured_site_url = (getattr(settings, 'SITE_URL', '') or '').strip().rstrip('/')
    if configured_site_url:
        return configured_site_url
    return f'{request.scheme}://{request.get_host()}'


def get_canonical_url(request):
    base = get_site_base_url(request)
    return f'{base}{request.path}'
