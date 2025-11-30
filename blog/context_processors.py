from django.conf import settings


def site_info(request):
    return {
        "site_name": getattr(settings, "SITE_NAME", "DjangoBlog"),
        "site_description": getattr(
            settings, "SITE_DESCRIPTION", "A professional blogging platform"
        ),
    }
