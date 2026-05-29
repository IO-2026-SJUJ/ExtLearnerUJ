"""
Dekoratory widoków. Zastępują Djangowe @login_required — nasza autentykacja
jest niezależna od Django auth (patrz middleware.py).
"""
from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect


def session_login_required(view_func):
    """Chroniony widok — wymaga zalogowanego użytkownika."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.app_user is None:
            return redirect('login')
        if not request.app_user.emailVerified:
            return redirect('verify_email')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*role_classes):
    """Wymaga, żeby request.app_user był instancją jednej z podanych ról."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.app_user is None:
                return redirect('login')
            if not isinstance(request.app_user, role_classes):
                return HttpResponseForbidden('Brak uprawnień do tej strony.')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def anonymous_required(view_func):
    """Odwrotność login_required — np. strona logowania niedostępna dla
    już zalogowanych (przekierowuje na dashboard)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.app_user is not None:
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
