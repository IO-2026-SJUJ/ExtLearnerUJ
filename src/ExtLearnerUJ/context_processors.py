"""Context processory — dane dostępne we wszystkich szablonach."""


def app_user(request):
    """Udostępnia `app_user` i `app_session` w szablonach.
    Dzięki temu base.html może pokazywać stan zalogowania."""
    user = getattr(request, 'app_user', None)

    # Flagi ról — używane w base.html do wyboru widocznej nawigacji.
    # Sprawdzamy przez nazwę klasy, żeby nie importować Moderator/Admin
    # (import cykliczny).
    is_moderator = False
    is_admin = False
    unread_notifications = 0
    if user is not None:
        cls_name = user.__class__.__name__
        is_moderator = cls_name in ('Moderator', 'Admin')
        is_admin = cls_name == 'Admin'
        # Licznik nieprzeczytanych powiadomień
        try:
            from .models import Notification
            unread_notifications = Notification.objects.filter(
                userId=user.email, isRead=False,
            ).count()
        except Exception:
            unread_notifications = 0

    return {
        'app_user': user,
        'app_session': getattr(request, 'app_session', None),
        'is_moderator': is_moderator,
        'is_admin': is_admin,
        'unread_notifications': unread_notifications,
    }
