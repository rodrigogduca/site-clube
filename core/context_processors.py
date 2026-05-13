from .utils import get_site_base_url, get_canonical_url


def site_meta(request):
    return {
        'site_url': get_site_base_url(request),
        'canonical_url': get_canonical_url(request),
    }
