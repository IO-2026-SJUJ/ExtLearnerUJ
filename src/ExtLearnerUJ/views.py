"""
Widoki dla Sprintu 1.

Flow:
    landing → register → verify_email → login → dashboard
        dashboard → diagnostic_start → diagnostic_test → diagnostic_result
        dashboard → materials_list → material_detail
"""
from __future__ import annotations

import json

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .decorators import session_login_required, anonymous_required, role_required
from .forms import RegisterForm, LoginForm, VerifyEmailForm
from .models import (
    User, Student, Session, EmailVerificationToken,
    Material, DiagnosticTest, DiagnosticResult,
)
from .services import GradingService


# ============================================================
# Landing
# ============================================================
def landing(request):
    if request.app_user is not None:
        return redirect('dashboard')
    return render(request, 'ExtLearnerUJ/landing.html')


# ============================================================
# Rejestracja — UC01
# ============================================================
@anonymous_required
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.register(
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                name=form.cleaned_data['name'],
            )
            if user is None:
                messages.error(request, 'Konto z tym adresem już istnieje.')
            else:
                # Zapisujemy email w sesji Django (nie mylić z naszą Session),
                # żeby strona verify_email wiedziała, kogo weryfikować.
                request.session['pending_verification_email'] = user.email
                messages.success(
                    request,
                    'Konto utworzone. Sprawdź e-mail i wpisz kod weryfikacyjny.'
                )
                return redirect('verify_email')
    else:
        form = RegisterForm()

    return render(request, 'ExtLearnerUJ/auth/register.html', {'form': form})


# ============================================================
# Weryfikacja email — UC02
# ============================================================
def verify_email_view(request):
    # Email do zweryfikowania bierzemy albo z naszej sesji (świeża
    # rejestracja), albo od zalogowanego-ale-niezweryfikowanego usera.
    email = None
    if request.app_user is not None and not request.app_user.emailVerified:
        email = request.app_user.email
    else:
        email = request.session.get('pending_verification_email')

    if not email:
        messages.info(request, 'Zaloguj się, aby zweryfikować konto.')
        return redirect('login')

    if request.method == 'POST':
        form = VerifyEmailForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, 'Nie znaleziono konta.')
                return redirect('register')

            if user.verifyEmail(form.cleaned_data['code']):
                request.session.pop('pending_verification_email', None)
                messages.success(request, 'Konto aktywowane. Możesz się zalogować.')
                return redirect('login')
            else:
                messages.error(request, 'Nieprawidłowy lub wygasły kod.')
    else:
        form = VerifyEmailForm()

    return render(request, 'ExtLearnerUJ/auth/verify_email.html', {
        'form': form, 'email': email,
    })


# ============================================================
# Logowanie — UC03
# ============================================================
@anonymous_required
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            session = User.authenticate(
                form.cleaned_data['email'],
                form.cleaned_data['password'],
            )
            if session is None:
                # Sprawdźmy, czy konto istnieje ale nie jest zweryfikowane
                try:
                    u = User.objects.get(email=form.cleaned_data['email'])
                    if not u.emailVerified:
                        request.session['pending_verification_email'] = u.email
                        messages.warning(
                            request,
                            'Najpierw zweryfikuj e-mail — sprawdź skrzynkę.'
                        )
                        return redirect('verify_email')
                except User.DoesNotExist:
                    pass
                messages.error(request, 'Nieprawidłowy e-mail lub hasło.')
            else:
                response = redirect('dashboard')
                response.set_cookie(
                    settings.SESSION_COOKIE_NAME_APP,
                    session.token,
                    max_age=settings.SESSION_LIFETIME_HOURS * 3600,
                    httponly=True,
                    secure=settings.SECURE_COOKIES,
                    samesite='Lax',
                )
                messages.success(request, f'Witaj z powrotem!')
                return response
    else:
        form = LoginForm()

    return render(request, 'ExtLearnerUJ/auth/login.html', {'form': form})


# ============================================================
# Wylogowanie
# ============================================================
@require_POST
@session_login_required
def logout_view(request):
    request.app_user.logout()
    response = redirect('landing')
    response.delete_cookie(settings.SESSION_COOKIE_NAME_APP)
    messages.info(request, 'Wylogowano.')
    return response


# ============================================================
# Dashboard
# ============================================================
@session_login_required
def dashboard(request):
    # Czy student ma już wynik diagnostyczny?
    last_diagnostic = (
        DiagnosticResult.objects
        .filter(userId=request.app_user.email)
        .order_by('-completedAt')
        .first()
    )

    # Ostatnie materiały (Sprint 1 — lista prosta)
    recent_materials = Material.objects.all()[:6]

    return render(request, 'ExtLearnerUJ/dashboard.html', {
        'last_diagnostic': last_diagnostic,
        'recent_materials': recent_materials,
    })


# ============================================================
# Test diagnostyczny — UC04 + UC05
# ============================================================
@session_login_required
@role_required(Student)
def diagnostic_start(request):
    """Strona intro + rozpoczęcie testu."""
    test = DiagnosticTest.objects.first()
    if test is None:
        messages.error(
            request,
            'Brak dostępnego testu diagnostycznego. Uruchom `python manage.py seed_diagnostic`.'
        )
        return redirect('dashboard')

    if request.method == 'POST':
        return redirect('diagnostic_test', test_id=test.id)

    question_count = test.questions.count()
    return render(request, 'ExtLearnerUJ/diagnostic/start.html', {
        'test': test,
        'question_count': question_count,
    })


@session_login_required
@role_required(Student)
def diagnostic_test(request, test_id):
    """Właściwy test — wyświetla pytania, przyjmuje odpowiedzi."""
    test = get_object_or_404(DiagnosticTest, pk=test_id)
    questions = list(test.questions.all())

    if request.method == 'POST':
        # Zbieramy odpowiedzi z formularza
        answers = {
            str(q.id): request.POST.get(f'q_{q.id}', '').strip()
            for q in questions
        }

        # Ocenianie przez serwis (Strategy pattern)
        result = GradingService().autoGradeDiagnostic(
            testId=test.id,
            answers=answers,
            userId=request.app_user.email,
        )
        if result is None:
            messages.error(request, 'Błąd oceniania testu.')
            return redirect('dashboard')

        return redirect('diagnostic_result', result_id=result.id)

    return render(request, 'ExtLearnerUJ/diagnostic/test.html', {
        'test': test,
        'questions': questions,
    })


@session_login_required
@role_required(Student)
def diagnostic_result(request, result_id):
    """Ekran wyników z wykresem obszarów."""
    result = get_object_or_404(
        DiagnosticResult, pk=result_id, userId=request.app_user.email,
    )
    weak_areas = result.getWeakAreas()

    # Przygotowanie danych do wykresu (JSON dla JS)
    chart_data = json.dumps([
        {'area': area, 'score': score}
        for area, score in sorted(result.areaScores.items())
    ])

    return render(request, 'ExtLearnerUJ/diagnostic/result.html', {
        'result': result,
        'weak_areas': weak_areas,
        'chart_data': chart_data,
    })


@require_POST
@session_login_required
def diagnostic_autosave(request, test_id):
    """Endpoint dla JS — autozapis postępu testu (NFR-02).
    Zapisuje stan w sesji Django (lekkie, nie wymaga tabeli)."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return HttpResponseBadRequest('Invalid JSON')

    answers = payload.get('answers', {})
    if not isinstance(answers, dict):
        return HttpResponseBadRequest('Invalid payload')

    key = f'diagnostic_progress_{test_id}'
    request.session[key] = answers
    return JsonResponse({'ok': True, 'saved_answers': len(answers)})


# ============================================================
# Materiały — UC07 + UC09 (lista i szczegóły)
# ============================================================
@session_login_required
def materials_list(request):
    category = request.GET.get('category', '').strip()
    status_filter = request.GET.get('status', '').strip()

    qs = Material.objects.all()
    if category:
        qs = qs.filter(category=category)
    if status_filter == 'verified':
        qs = qs.filter(isVerified=True)
    elif status_filter == 'pending':
        qs = qs.filter(status=Material.STATUS_PENDING)

    categories = ['grammar', 'reading', 'listening', 'vocabulary']

    return render(request, 'ExtLearnerUJ/materials/list.html', {
        'materials': qs,
        'categories': categories,
        'current_category': category,
        'current_status': status_filter,
    })


@session_login_required
def material_detail(request, material_id):
    material = get_object_or_404(Material, pk=material_id)
    return render(request, 'ExtLearnerUJ/materials/detail.html', {
        'material': material,
    })


# ============================================================
# Healthcheck (przydaje się w CI)
# ============================================================
def healthcheck(request):
    return JsonResponse({'status': 'ok'})
