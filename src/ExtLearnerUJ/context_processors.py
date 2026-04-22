"""Context processory — dane dostępne we wszystkich szablonach."""


def app_user(request):
    """Udostępnia `app_user` i `app_session` w szablonach.
    Dzięki temu base.html może pokazywać stan zalogowania."""
    return {
        'app_user': getattr(request, 'app_user', None),
        'app_session': getattr(request, 'app_session', None),
    }
