"""
SessionAuthMiddleware — ustawia `request.app_user` na podstawie ciasteczka
`session_token`. Używa naszego modelu Session (patrz models.py), nie
korzystamy z Django auth framework.

Używamy nazwy `app_user` a nie `user`, żeby nie nadpisać obiektu z Django
auth — `/admin/` Django nadal powinien działać dla superusera.
"""
from django.conf import settings
from django.utils import timezone

from .models import User, Student, Moderator, Admin, Session


class SessionAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.app_user = None
        request.app_session = None

        token = request.COOKIES.get(settings.SESSION_COOKIE_NAME_APP)
        if token:
            try:
                session = Session.objects.get(token=token)
            except Session.DoesNotExist:
                return self._clear_and_continue(request)

            if not session.is_valid():
                session.invalidate()
                return self._clear_and_continue(request)

            try:
                user = User.objects.get(email=session.userId)
            except User.DoesNotExist:
                session.invalidate()
                return self._clear_and_continue(request)

            # Rozstrzygamy rolę — zwracamy najbardziej konkretną instancję
            request.app_user = self._resolve_role(user)
            request.app_session = session

            # Auto-refresh sesji gdy zostało <1h
            session.refresh()

        response = self.get_response(request)
        return response

    def _clear_and_continue(self, request):
        response = self.get_response(request)
        # Usuń niepoprawne ciasteczko u klienta
        response.delete_cookie(settings.SESSION_COOKIE_NAME_APP)
        return response

    @staticmethod
    def _resolve_role(user: User) -> User:
        """Zwraca najbardziej konkretną instancję roli (Student/Moderator/Admin)
        jeśli istnieje. Multi-table inheritance → sprawdzamy tabele potomne."""
        pk = user.pk
        for cls in (Admin, Moderator, Student):
            try:
                return cls.objects.get(pk=pk)
            except cls.DoesNotExist:
                continue
        return user
