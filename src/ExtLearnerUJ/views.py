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
from .forms import (
    RegisterForm, LoginForm, VerifyEmailForm,
    MaterialForm, ReportForm, VerifyMaterialForm,
    WorkForm, WorkReviewForm, AdminBlockUserForm, ReviewReportForm,
    ModeratorApplicationForm, ReviewApplicationForm,
    ForgotPasswordForm, ResetPasswordForm,
)
from .models import (
    User, Student, Moderator, Admin, Session, EmailVerificationToken,
    Material, DiagnosticTest, DiagnosticResult,
    Vote, Notification, MaterialVerification, Report, Comment,
    Work, Package, PaymentTransaction, WorkReview, ErrorMark, FileAttachment,
    Test, ExamAttempt, UserStats, Payout, ModeratorApplication,
    PasswordResetToken, ModeratorRating,
)
from .services import (
    GradingService, RecommendationService, StatisticsService, RankingService,
    ReportGenerator,
)


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


@require_POST
def resend_verification_code(request):
    """Ponowne wysłanie kodu weryfikacyjnego na adres oczekujący weryfikacji."""
    if request.app_user is not None and not request.app_user.emailVerified:
        email = request.app_user.email
    else:
        email = request.session.get('pending_verification_email')

    if not email:
        messages.info(request, 'Zaloguj się, aby zweryfikować konto.')
        return redirect('login')

    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        messages.error(request, 'Nie znaleziono konta.')
        return redirect('register')

    if user.sendVerificationCode():
        request.session['pending_verification_email'] = user.email
        messages.success(request, 'Wysłaliśmy nowy kod — sprawdź skrzynkę (i spam).')
    else:
        messages.info(request, 'To konto jest już zweryfikowane. Możesz się zalogować.')
        return redirect('login')
    return redirect('verify_email')


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
                # Diagnozujemy powód odmowy: niezweryfikowany / zablokowany.
                u = User.objects.filter(
                    email__iexact=form.cleaned_data['email']
                ).first()
                if u is not None and u.status == User.STATUS_BLOCKED and not u.is_block_expired():
                    if u.blockedUntil:
                        from django.utils import timezone as _tz
                        until = _tz.localtime(u.blockedUntil).strftime('%d.%m.%Y %H:%M')
                        messages.error(
                            request,
                            f'To konto jest zablokowane do {until}.'
                        )
                    else:
                        messages.error(
                            request,
                            'To konto zostało zablokowane bezterminowo. '
                            'Skontaktuj się z administracją.'
                        )
                elif u is not None and not u.emailVerified:
                    request.session['pending_verification_email'] = u.email
                    messages.warning(
                        request,
                        'Najpierw zweryfikuj e-mail — sprawdź skrzynkę.'
                    )
                    return redirect('verify_email')
                else:
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
# Reset hasła — „Zapomniałem hasła"
# ============================================================
@anonymous_required
def forgot_password_view(request):
    """Krok 1: podaj e-mail → wysyłamy link z tokenem (jeśli konto istnieje)."""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email__iexact=email).first()
            # Nie zdradzamy, czy konto istnieje (ochrona prywatności).
            if user is not None:
                token = PasswordResetToken.issue(user.email)
                reset_url = request.build_absolute_uri(
                    reverse('reset_password', args=[token.token])
                )
                from django.core.mail import send_mail
                send_mail(
                    'ExtLearnerUJ — reset hasła',
                    (f'Cześć {user.name}!\n\n'
                     f'Aby ustawić nowe hasło, kliknij w link (ważny 1 godzinę):\n'
                     f'{reset_url}\n\n'
                     f'Jeśli to nie Ty prosiłeś/aś o reset — zignoruj tę wiadomość.'),
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                )
            messages.success(
                request,
                'Jeśli konto o tym adresie istnieje, wysłaliśmy link do resetu hasła.'
            )
            return redirect('login')
    else:
        form = ForgotPasswordForm()
    return render(request, 'ExtLearnerUJ/auth/forgot_password.html', {'form': form})


@anonymous_required
def reset_password_view(request, token):
    """Krok 2: link z tokenem → ustaw nowe hasło."""
    reset = PasswordResetToken.objects.filter(token=token).first()
    if reset is None or not reset.is_valid():
        messages.error(request, 'Link do resetu jest nieprawidłowy lub wygasł.')
        return redirect('forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user = User.objects.filter(email__iexact=reset.userId).first()
            if user is None:
                messages.error(request, 'Nie znaleziono konta.')
                return redirect('forgot_password')
            from django.contrib.auth.hashers import make_password
            user.password = make_password(form.cleaned_data['password'])
            # Kliknięcie linku z maila dowodzi, że użytkownik kontroluje skrzynkę,
            # więc przy okazji potwierdzamy adres (nie zmuszamy do ponownej
            # weryfikacji po resecie).
            update_fields = ['password']
            if not user.emailVerified:
                user.emailVerified = True
                update_fields.append('emailVerified')
            user.save(update_fields=update_fields)
            reset.used = True
            reset.save(update_fields=['used'])
            # Reset hasła unieważnia istniejące sesje (bezpieczeństwo).
            Session.objects.filter(userId=user.email).delete()
            messages.success(request, 'Hasło zmienione. Możesz się zalogować.')
            return redirect('login')
    else:
        form = ResetPasswordForm()
    return render(request, 'ExtLearnerUJ/auth/reset_password.html', {
        'form': form, 'token': token,
    })


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
# Usunięcie konta (RODO — prawo do bycia zapomnianym)
# ============================================================
@session_login_required
def delete_account_view(request):
    """Trwałe usunięcie konta i wszystkich danych użytkownika.
    Dla bezpieczeństwa wymagamy potwierdzenia hasłem."""
    if request.method == 'POST':
        from django.contrib.auth.hashers import check_password
        password = request.POST.get('password', '')
        if not check_password(password, request.app_user.password):
            messages.error(request, 'Nieprawidłowe hasło — konto NIE zostało usunięte.')
            return render(request, 'ExtLearnerUJ/auth/delete_account.html')
        ok = request.app_user.deleteAccount()
        if not ok:
            messages.error(request, 'Nie udało się usunąć konta. Spróbuj ponownie.')
            return render(request, 'ExtLearnerUJ/auth/delete_account.html')
        response = redirect('landing')
        response.delete_cookie(settings.SESSION_COOKIE_NAME_APP)
        messages.success(
            request,
            'Twoje konto i wszystkie powiązane dane zostały trwale usunięte.'
        )
        return response
    return render(request, 'ExtLearnerUJ/auth/delete_account.html')


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

    # FR-05: rekomendacje materiałów z najsłabszych obszarów diagnostyki
    # (dostępne dla każdej roli — wszyscy mogą się uczyć).
    recommendations = request.app_user.viewRecommendations()

    # Ostatnie materiały (Sprint 1 — lista prosta)
    recent_materials = Material.objects.all()[:6]

    return render(request, 'ExtLearnerUJ/dashboard.html', {
        'last_diagnostic': last_diagnostic,
        'recent_materials': recent_materials,
        'recommendations': recommendations,
    })


# ============================================================
# Test diagnostyczny — UC04 + UC05
# ============================================================
@session_login_required
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
    mine = request.GET.get('mine', '').strip()  # '1' → tylko moje materiały

    qs = Material.objects.all()
    if mine == '1':
        qs = qs.filter(authorId=request.app_user.email)
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
        'mine': mine == '1',
    })


@session_login_required
def material_detail(request, material_id):
    material = get_object_or_404(Material, pk=material_id)
    # Czy aktualny user już głosował?
    user_voted = Vote.objects.filter(
        userId=request.app_user.email, materialId=str(material_id)
    ).exists()
    vote_count = Vote.objects.filter(materialId=str(material_id)).count()
    is_owner = material.authorId == request.app_user.email
    can_delete = is_owner or isinstance(request.app_user, Admin)
    return render(request, 'ExtLearnerUJ/materials/detail.html', {
        'material': material,
        'user_voted': user_voted,
        'vote_count': vote_count,
        'is_owner': is_owner,
        'can_delete': can_delete,
    })


@require_POST
@session_login_required
def material_delete(request, material_id):
    """Usunięcie materiału — przez autora (własny) lub admina (dowolny)."""
    material = get_object_or_404(Material, pk=material_id)
    is_owner = material.authorId == request.app_user.email
    if isinstance(request.app_user, Admin) and not is_owner:
        request.app_user.deleteMaterial(material_id, reason='Decyzja administratora')
        messages.success(request, 'Materiał usunięty.')
    elif is_owner:
        request.app_user.deleteOwnMaterial(material_id)
        messages.success(request, 'Twój materiał został usunięty.')
    else:
        messages.error(request, 'Brak uprawnień do usunięcia tego materiału.')
        return redirect('material_detail', material_id=material_id)
    return redirect('materials_list')


# ============================================================
# Sprint 2 — dodawanie materiałów (FR-08)
# ============================================================
@session_login_required
def material_create(request):
    """Student dodaje własny materiał. Materiał ląduje ze statusem PENDING
    i czeka na weryfikację moderatora (UC16)."""
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES)
        if form.is_valid():
            files = []
            if form.cleaned_data.get('attachment'):
                files = [form.cleaned_data['attachment']]
            material = Material.create(
                data={
                    'title': form.cleaned_data['title'],
                    'content': form.cleaned_data['content'],
                    'authorId': request.app_user.email,
                    'category': form.cleaned_data['category'],
                },
                files=files,
            )
            messages.success(
                request,
                'Materiał dodany. Czeka na weryfikację przez moderatora.',
            )
            return redirect('material_detail', material_id=material.id)
    else:
        form = MaterialForm()

    return render(request, 'ExtLearnerUJ/materials/new.html', {'form': form})


# ============================================================
# Sprint 2 — głosowanie (FR-09)
# ============================================================
@require_POST
@session_login_required
def material_vote(request, material_id):
    """AJAX endpoint — oddaje głos na materiał.
    Idempotentny: drugi raz nic nie robi.
    Zwraca JSON z aktualnym priorytetem i informacją czy user już głosował."""
    vote = request.app_user.voteMaterial(material_id)
    if vote is None:
        return JsonResponse({'error': 'Materiał nie istnieje'}, status=404)

    material = Material.objects.get(pk=material_id)
    vote_count = Vote.objects.filter(materialId=str(material_id)).count()
    return JsonResponse({
        'ok': True,
        'priority': material.priority,
        'voteCount': vote_count,
        'userVoted': True,
    })


# ============================================================
# Sprint 2 — zgłaszanie (FR-13, UC25)
# ============================================================
@session_login_required
def report_material(request, material_id):
    """Student zgłasza materiał z błędami lub spam (FR-13)."""
    material = get_object_or_404(Material, pk=material_id)

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            request.app_user.submitReport(
                targetType=Report.TARGET_MATERIAL,
                targetId=material_id,
                reason=form.cleaned_data['reason'],
            )
            # Powiadomienie dla zgłaszającego — potwierdzenie przyjęcia
            Notification.objects.create(
                userId=request.app_user.email,
                message=(
                    f'✓ Twoje zgłoszenie materiału "{material.title}" '
                    f'zostało przyjęte. Administrator rozpatrzy je w ciągu 48h.'
                ),
            )
            messages.success(
                request,
                'Zgłoszenie wysłane. Administrator rozpatrzy je w ciągu 48h.',
            )
            return redirect('material_detail', material_id=material_id)
    else:
        form = ReportForm()

    return render(request, 'ExtLearnerUJ/materials/report.html', {
        'form': form, 'material': material,
    })


# ============================================================
# Sprint 2 — panel moderatora (UC36, UC31, UC32, UC33)
# ============================================================
@session_login_required
@role_required(Moderator, Admin)
def moderator_dashboard(request):
    """Strona startowa panelu moderatora."""
    pending_count = Material.objects.filter(
        status=Material.STATUS_PENDING
    ).count()
    verified_by_me = MaterialVerification.objects.filter(
        moderatorId=request.app_user.email,
    ).count()
    return render(request, 'ExtLearnerUJ/moderator/dashboard.html', {
        'pending_count': pending_count,
        'verified_by_me': verified_by_me,
    })


@session_login_required
@role_required(Moderator, Admin)
def moderator_materials_queue(request):
    """Kolejka materiałów do weryfikacji, posortowana po priorytecie (UC36)."""
    materials = request.app_user.viewMaterialsToVerify() \
        if isinstance(request.app_user, Moderator) \
        else list(Material.objects.filter(status=Material.STATUS_PENDING)
                  .order_by('-priority', 'createdAt'))
    return render(request, 'ExtLearnerUJ/moderator/materials_queue.html', {
        'materials': materials,
    })


@session_login_required
@role_required(Moderator, Admin)
def moderator_verify_material(request, material_id):
    """Widok weryfikacji pojedynczego materiału (UC31)."""
    material = get_object_or_404(Material, pk=material_id)

    if request.method == 'POST':
        form = VerifyMaterialForm(request.POST)
        if form.is_valid():
            # Admin może działać jako moderator — ale bezpieczniej przepuścić
            # przez Moderator method jeśli user jest instancją Moderator.
            if isinstance(request.app_user, Moderator):
                request.app_user.verifyMaterial(
                    materialId=material_id,
                    decision=form.cleaned_data['decision'],
                    comment=form.cleaned_data.get('comment', ''),
                )
            else:
                # Admin — wywołujemy logikę przez proxy
                _admin_verify_material(
                    admin_email=request.app_user.email,
                    material=material,
                    decision=form.cleaned_data['decision'],
                    comment=form.cleaned_data.get('comment', ''),
                )
            messages.success(request, 'Decyzja zapisana.')
            return redirect('moderator_materials_queue')
    else:
        form = VerifyMaterialForm()

    return render(request, 'ExtLearnerUJ/moderator/verify_material.html', {
        'material': material, 'form': form,
    })


def _admin_verify_material(admin_email, material, decision, comment):
    """Pomocnik — admin działa jak moderator."""
    verification = MaterialVerification.objects.create(
        materialId=str(material.id),
        moderatorId=admin_email,
        decision=decision,
        comment=comment,
    )
    if decision == MaterialVerification.DECISION_ACCEPTED:
        material.status = Material.STATUS_VERIFIED
        material.isVerified = True
    elif decision == MaterialVerification.DECISION_REJECTED:
        material.status = Material.STATUS_REJECTED
        material.isVerified = False
    material.save(update_fields=['status', 'isVerified'])

    msg_map = {
        'ACCEPTED': f'Twój materiał "{material.title}" został zaakceptowany ✓',
        'REJECTED': f'Twój materiał "{material.title}" został odrzucony',
        'NEEDS_REVISION': f'Twój materiał "{material.title}" wymaga poprawy',
    }
    Notification.objects.create(
        userId=material.authorId,
        message=msg_map.get(decision, ''),
    )
    if comment:
        Comment.objects.create(
            authorId=admin_email,
            targetType='MATERIAL',
            targetId=str(material.id),
            text=comment,
        )
    return verification


# ============================================================
# Sprint 2 — notyfikacje (UC32)
# ============================================================
@session_login_required
def notifications_list(request):
    notifications = Notification.objects.filter(userId=request.app_user.email)
    has_unread = notifications.filter(isRead=False).exists()
    return render(request, 'ExtLearnerUJ/notifications/list.html', {
        'notifications': notifications,
        'has_unread': has_unread,
    })


@require_POST
@session_login_required
def notification_mark_read(request, notification_id):
    try:
        n = Notification.objects.get(pk=notification_id, userId=request.app_user.email)
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)
    n.markAsRead()
    return JsonResponse({'ok': True})


@require_POST
@session_login_required
def notifications_mark_all_read(request):
    """Oznacza wszystkie powiadomienia użytkownika jako przeczytane."""
    Notification.objects.filter(
        userId=request.app_user.email, isRead=False,
    ).update(isRead=True)
    messages.success(request, 'Wszystkie powiadomienia oznaczone jako przeczytane.')
    return redirect('notifications_list')


# ============================================================
# Healthcheck (przydaje się w CI)
# ============================================================
def healthcheck(request):
    return JsonResponse({'status': 'ok'})


# ============================================================
# Sprint 2 · tydzień 2 — Prace pisemne (FR-15, UC19/UC20/UC21)
# ============================================================
@session_login_required
def work_new(request):
    """Student wysyła pracę pisemną do sprawdzenia."""
    # Czy są jakieś pakiety? Jeśli nie — poproś o seed.
    if not Package.objects.exists():
        messages.error(
            request,
            'Brak pakietów sprawdzenia. Uruchom `python manage.py seed_packages`.'
        )
        return redirect('dashboard')

    if request.method == 'POST':
        form = WorkForm(request.POST, request.FILES)
        if form.is_valid():
            files = []
            if form.cleaned_data.get('attachment'):
                files = [form.cleaned_data['attachment']]

            work = request.app_user.submitWork(
                workData={
                    'title': form.cleaned_data['title'],
                    'description': form.cleaned_data.get('description', ''),
                },
                packageId=form.cleaned_data['package'].id,
                files=files,
            )
            if work is None:
                messages.error(request, 'Błąd tworzenia pracy.')
                return redirect('work_new')
            return redirect('work_payment', work_id=work.id)
    else:
        form = WorkForm()

    return render(request, 'ExtLearnerUJ/works/new.html', {'form': form})


@session_login_required
def work_payment(request, work_id):
    """Ekran rozliczenia. Bramki płatności (BLIK/karta/przelew) są obecnie
    niedostępne — jedyna aktywna opcja to rozliczenie indywidualne:
    sprawdzający po rezerwacji pracy kontaktuje się ze zleceniodawcą
    (widzi jego e-mail) i ustalają płatność między sobą."""
    work = get_object_or_404(Work, pk=work_id, studentId=request.app_user.email)

    if work.status != Work.STATUS_PENDING_PAYMENT:
        messages.info(request, 'Ta praca jest już zgłoszona do sprawdzenia.')
        return redirect('work_detail', work_id=work.id)

    package = get_object_or_404(Package, pk=work.packageId)

    if request.method == 'POST':
        method = request.POST.get('method', '')

        if method != PaymentTransaction.METHOD_DIRECT:
            messages.error(
                request,
                'Wybrana metoda płatności jest obecnie niedostępna. '
                'Skorzystaj z rozliczenia indywidualnego.'
            )
        else:
            PaymentTransaction.objects.create(
                workId=str(work.id),
                userId=request.app_user.email,
                amount=package.price,
                method=PaymentTransaction.METHOD_DIRECT,
            )
            work.status = Work.STATUS_PAID
            work.save(update_fields=['status'])
            messages.success(
                request,
                'Praca zgłoszona do sprawdzenia. Gdy sprawdzający ją '
                'zarezerwuje, dostaniesz powiadomienie z jego adresem '
                'e-mail — płatność ustalicie bezpośrednio między sobą.'
            )
            return redirect('work_detail', work_id=work.id)

    return render(request, 'ExtLearnerUJ/works/payment.html', {
        'work': work, 'package': package,
    })


@session_login_required
def work_detail(request, work_id):
    """Widok pracy — pokazuje status, a jeśli jest review to feedback."""
    work = get_object_or_404(Work, pk=work_id, studentId=request.app_user.email)
    package = Package.objects.filter(pk=work.packageId).first()
    review = WorkReview.objects.filter(
        workId=str(work.id), status=WorkReview.STATUS_PUBLISHED,
    ).first()
    error_marks = []
    if review:
        error_marks = ErrorMark.objects.filter(reviewId=str(review.id))

    my_rating = ModeratorRating.objects.filter(
        workId=str(work.id), studentId=request.app_user.email,
    ).first()

    return render(request, 'ExtLearnerUJ/works/detail.html', {
        'work': work, 'package': package, 'review': review,
        'error_marks': error_marks, 'my_rating': my_rating,
    })


@require_POST
@session_login_required
def rate_moderator_view(request, work_id):
    """Zleceniodawca ocenia sprawdzającego (1-5 gwiazdek) po otrzymaniu
    opublikowanej oceny pracy."""
    rating = request.app_user.rateModerator(
        work_id,
        request.POST.get('score'),
        request.POST.get('comment', '').strip(),
    )
    if rating is None:
        messages.error(
            request,
            'Nie udało się zapisać oceny. Ocenić można po otrzymaniu '
            'sprawdzonej pracy (skala 1-5).'
        )
    else:
        messages.success(request, 'Dziękujemy za ocenę sprawdzającego!')
    return redirect('work_detail', work_id=work_id)


@session_login_required
def my_works(request):
    """Lista moich prac."""
    works = Work.objects.filter(studentId=request.app_user.email)
    return render(request, 'ExtLearnerUJ/works/my_list.html', {'works': works})


# ============================================================
# Sprint 2 · tydzień 2 — Moderator: prace (UC38, UC39, UC40)
# ============================================================
@session_login_required
@role_required(Moderator, Admin)
def moderator_works_queue(request):
    """Kolejka prac do sprawdzenia."""
    if isinstance(request.app_user, Moderator):
        works = request.app_user.viewWorksToCheck()
    else:
        # Admin — widzi wszystko
        works = list(
            Work.objects.filter(
                status__in=[Work.STATUS_PAID, Work.STATUS_IN_REVIEW]
            ).order_by('submittedAt')
        )
    # Zarobek za pracę = pełna cena pakietu (bez marży) — pokazujemy
    # przy doborze pracy, ile sprawdzający na niej zarobi.
    prices = {str(p.id): p.price for p in Package.objects.all()}
    for w in works:
        w.earn_amount = prices.get(str(w.packageId), 0.0)
    return render(request, 'ExtLearnerUJ/moderator/works_queue.html', {
        'works': works,
    })


@require_POST
@session_login_required
@role_required(Moderator, Admin)
def moderator_reserve_work(request, work_id):
    """Rezerwacja pracy do sprawdzenia (UC39). Wspólna ścieżka dla
    moderatora i admina — zawsze blokuje pracę dla innych i wysyła
    zleceniodawcy powiadomienie z kontaktem do sprawdzającego."""
    success = request.app_user.reserveWork(work_id)

    if success:
        messages.success(request, 'Praca zarezerwowana.')
        return redirect('moderator_work_editor', work_id=work_id)
    else:
        messages.error(
            request,
            'Nie udało się zarezerwować — ktoś mógł Cię wyprzedzić.'
        )
        return redirect('moderator_works_queue')


@session_login_required
@role_required(Moderator, Admin)
def moderator_work_editor(request, work_id):
    """Edytor oceny pracy z zaznaczaniem błędów (FR-10)."""
    work = get_object_or_404(Work, pk=work_id)

    # Sprawdź dostęp: praca musi być przypisana do aktualnego moderatora
    # (admin ma wolną rękę)
    if (not isinstance(request.app_user, Admin)
            and work.assignedModeratorId != request.app_user.email):
        messages.error(request, 'Ta praca nie jest przypisana do Ciebie.')
        return redirect('moderator_works_queue')

    # Czy szkic już istnieje?
    review, _ = WorkReview.objects.get_or_create(
        workId=str(work.id),
        moderatorId=request.app_user.email,
        defaults={'status': WorkReview.STATUS_DRAFT},
    )
    error_marks = ErrorMark.objects.filter(reviewId=str(review.id))

    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        form = WorkReviewForm(request.POST)
        if form.is_valid():
            review.grade = form.cleaned_data['grade']
            review.generalComment = form.cleaned_data['generalComment']
            review.save(update_fields=['grade', 'generalComment'])

            if action == 'publish':
                review.publish()
                messages.success(
                    request,
                    'Ocena opublikowana. Student został powiadomiony.',
                )
                return redirect('moderator_works_queue')
            else:
                messages.success(request, 'Szkic zapisany.')
                return redirect('moderator_work_editor', work_id=work_id)
    else:
        form = WorkReviewForm(initial={
            'grade': review.grade,
            'generalComment': review.generalComment,
        })

    return render(request, 'ExtLearnerUJ/moderator/work_editor.html', {
        'work': work, 'review': review, 'error_marks': error_marks,
        'form': form,
    })


@require_POST
@session_login_required
@role_required(Moderator, Admin)
def moderator_add_error_mark(request, review_id):
    """AJAX: dodaje zaznaczenie błędu w edytorze."""
    try:
        review = WorkReview.objects.get(
            pk=review_id, moderatorId=request.app_user.email,
        )
    except WorkReview.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return HttpResponseBadRequest('Invalid JSON')

    snippet = payload.get('snippet', '').strip()
    mark_type = payload.get('type', ErrorMark.TYPE_GRAMMAR)
    position = payload.get('position', '')
    comment = payload.get('comment', '')

    if not snippet or mark_type not in dict(ErrorMark.TYPE_CHOICES):
        return HttpResponseBadRequest('Invalid payload')

    mark = review.addErrorMark(
        textSnippet=snippet, mark_type=mark_type, positionInText=position,
    )
    if comment:
        mark.comment = comment
        mark.save(update_fields=['comment'])

    return JsonResponse({
        'ok': True, 'id': mark.id,
        'snippet': mark.textSnippet, 'type': mark.type,
        'comment': mark.comment,
    })


@require_POST
@session_login_required
@role_required(Moderator, Admin)
def moderator_delete_error_mark(request, mark_id):
    """AJAX: usuwa zaznaczenie błędu."""
    try:
        mark = ErrorMark.objects.get(pk=mark_id)
        # Weryfikacja: mark musi należeć do review moderatora
        review = WorkReview.objects.get(
            pk=mark.reviewId, moderatorId=request.app_user.email,
        )
    except (ErrorMark.DoesNotExist, WorkReview.DoesNotExist):
        return JsonResponse({'error': 'not found'}, status=404)

    mark.delete()
    return JsonResponse({'ok': True})


# ============================================================
# Sprint 2 · tydzień 2 — Panel admina (FR-11, UC46, UC47, UC48)
# ============================================================
@session_login_required
@role_required(Admin)
def admin_dashboard(request):
    """Dashboard admina z metrykami systemu."""
    stats = request.app_user.viewSystemStats()
    return render(request, 'ExtLearnerUJ/admin_panel/dashboard.html', {
        'stats': stats,
    })


@session_login_required
@role_required(Admin)
def admin_reports_queue(request):
    """Kolejka zgłoszeń do rozpatrzenia (UC46)."""
    reports = request.app_user.handleUserReports()
    return render(request, 'ExtLearnerUJ/admin_panel/reports_queue.html', {
        'reports': reports,
    })


@session_login_required
@role_required(Admin)
def admin_review_report(request, report_id):
    """Rozpatrzenie pojedynczego zgłoszenia (UC47)."""
    report = get_object_or_404(Report, pk=report_id)

    # Podgląd obiektu, którego dotyczy zgłoszenie
    target = None
    target_author = None  # autor materiału — żeby admin mógł go zbanować
    if report.targetType == Report.TARGET_MATERIAL:
        try:
            target = Material.objects.get(pk=report.targetId)
            target_author = User.objects.filter(email=target.authorId).first()
        except Material.DoesNotExist:
            target = None
    elif report.targetType == Report.TARGET_USER:
        try:
            target = User.objects.get(email=report.targetId)
            target_author = target
        except User.DoesNotExist:
            target = None

    if request.method == 'POST':
        form = ReviewReportForm(request.POST)
        if form.is_valid():
            request.app_user.reviewReport(
                reportId=report_id,
                decision=form.cleaned_data['decision'],
                comment=form.cleaned_data.get('comment', ''),
            )
            messages.success(request, 'Zgłoszenie rozpatrzone.')
            return redirect('admin_reports_queue')
    else:
        form = ReviewReportForm()

    return render(request, 'ExtLearnerUJ/admin_panel/review_report.html', {
        'report': report, 'target': target, 'target_author': target_author,
        'form': form,
    })


@session_login_required
@role_required(Admin)
def admin_users_list(request):
    """Lista użytkowników (UC48) z filtrem roli (np. tylko moderatorzy)."""
    role = request.GET.get('role', '').strip()  # '' | 'moderator' | 'admin' | 'student'
    users = list(User.objects.all().order_by('-registrationDate'))
    mod_pks = set(Moderator.objects.values_list('pk', flat=True))
    admin_pks = set(Admin.objects.values_list('pk', flat=True))

    rows = []
    for u in users:
        if u.pk in admin_pks:
            r = 'admin'
        elif u.pk in mod_pks:
            r = 'moderator'
        else:
            r = 'student'
        if role and role != r:
            continue
        avg, cnt = (None, 0)
        if r in ('moderator', 'admin'):
            avg, cnt = ModeratorRating.average_for(u.email)
        rows.append({'user': u, 'role': r, 'rating_avg': avg, 'rating_count': cnt})

    return render(request, 'ExtLearnerUJ/admin_panel/users_list.html', {
        'rows': rows,
        'current_role': role,
    })


@session_login_required
@role_required(Admin)
def admin_user_detail(request, user_email):
    """Profil usera + akcje admina (blokada/odblokowanie)."""
    user = get_object_or_404(User, email=user_email)

    # Historia usera
    materials = Material.objects.filter(authorId=user.email)
    reports_made = Report.objects.filter(reporterId=user.email)
    reports_against = Report.objects.filter(
        targetType=Report.TARGET_USER, targetId=user.email,
    )

    if request.method == 'POST':
        form = AdminBlockUserForm(request.POST)
        if form.is_valid():
            duration = form.cleaned_data['duration']
            days = None if duration == 'permanent' else int(duration)
            request.app_user.manageUserAccount(
                userId=user.email,
                newStatus=User.STATUS_BLOCKED,
                days=days,
                reason=form.cleaned_data.get('reason', ''),
            )
            messages.success(
                request,
                f'Konto {user.email} zostało zablokowane.'
            )
            return redirect('admin_user_detail', user_email=user.email)
    else:
        form = AdminBlockUserForm()

    is_mod = Moderator.objects.filter(pk=user.pk).exists()
    rating_avg, rating_count = (None, 0)
    if is_mod or Admin.objects.filter(pk=user.pk).exists():
        rating_avg, rating_count = ModeratorRating.average_for(user.email)

    return render(request, 'ExtLearnerUJ/admin_panel/user_detail.html', {
        'target_user': user, 'materials': materials,
        'reports_made': reports_made, 'reports_against': reports_against,
        'form': form,
        'target_is_moderator': is_mod,
        'rating_avg': rating_avg, 'rating_count': rating_count,
    })


@require_POST
@session_login_required
@role_required(Admin)
def admin_unblock_user(request, user_email):
    """Odblokowanie konta."""
    request.app_user.manageUserAccount(
        userId=user_email, newStatus=User.STATUS_ACTIVE,
    )
    messages.success(request, f'Konto {user_email} odblokowane.')
    return redirect('admin_user_detail', user_email=user_email)


# ============================================================
# Sprint 3 — symulacja egzaminu z twardym timerem (FR-06)
# ============================================================
def _get_exam_test():
    """Zwraca aktywny test egzaminacyjny (pierwszy Test typu EXAM)."""
    return Test.objects.filter(type=Test.TYPE_EXAM).order_by('id').first()


@session_login_required
def exam_start(request):
    """Intro do symulacji egzaminu. POST tworzy nowe podejście z deadlinem."""
    test = _get_exam_test()
    if test is None:
        messages.error(
            request,
            'Brak symulacji egzaminu. Uruchom `python manage.py seed_exam`.'
        )
        return redirect('dashboard')

    # Czy jest niezakończone, jeszcze ważne podejście? Wróćmy do niego.
    ongoing = ExamAttempt.objects.filter(
        userId=request.app_user.email,
        testId=str(test.id),
        status=ExamAttempt.STATUS_IN_PROGRESS,
    ).first()
    if ongoing and not ongoing.is_expired():
        if request.method == 'POST':
            return redirect('exam_take', attempt_id=ongoing.id)

    if request.method == 'POST':
        # Domknij ewentualne wygasłe podejście, potem rozpocznij nowe.
        if ongoing and ongoing.is_expired():
            ongoing.submit()
        attempt = ExamAttempt.start(test, request.app_user.email)
        return redirect('exam_take', attempt_id=attempt.id)

    return render(request, 'ExtLearnerUJ/exam/start.html', {
        'test': test,
        'question_count': test.questions.count(),
        'duration': test.durationMinutes,
        'ongoing': ongoing if (ongoing and not ongoing.is_expired()) else None,
    })


@session_login_required
def exam_take(request, attempt_id):
    """Właściwa symulacja. Twardy timer egzekwowany serwerowo: jeśli minął
    deadline, podejście jest automatycznie zamykane i przekierowane do wyniku."""
    attempt = get_object_or_404(
        ExamAttempt, pk=attempt_id, userId=request.app_user.email,
    )

    # Już zakończone → wynik.
    if attempt.status == ExamAttempt.STATUS_SUBMITTED:
        return redirect('exam_result', attempt_id=attempt.id)

    # Czas minął → automatyczne zamknięcie (FR-06: po 0:00 brak możliwości
    # odpowiedzi, system wysyła wynik).
    if attempt.is_expired():
        attempt.submit()
        messages.info(request, 'Czas minął — egzamin został zakończony automatycznie.')
        return redirect('exam_result', attempt_id=attempt.id)

    test = get_object_or_404(Test, pk=attempt.testId)
    questions = list(test.questions.all())

    if request.method == 'POST':
        answers = {
            str(q.id): request.POST.get(f'q_{q.id}', '').strip()
            for q in questions
        }
        # Serwer ponownie sprawdza deadline — odrzucamy spóźnione odpowiedzi.
        if attempt.is_expired():
            attempt.submit()  # liczy z tego co było zautozapisane
            messages.info(request, 'Czas minął — liczymy zapisane odpowiedzi.')
        else:
            attempt.submit(answers)
        return redirect('exam_result', attempt_id=attempt.id)

    return render(request, 'ExtLearnerUJ/exam/take.html', {
        'attempt': attempt,
        'test': test,
        'questions': questions,
        'seconds_left': attempt.seconds_left(),
        'saved_answers': json.dumps(attempt.answers or {}),
    })


@require_POST
@session_login_required
def exam_autosave(request, attempt_id):
    """AJAX autozapis odpowiedzi egzaminu (NFR-02). Zwraca też pozostały czas,
    żeby klient mógł zsynchronizować zegar ze stanem serwera."""
    try:
        attempt = ExamAttempt.objects.get(
            pk=attempt_id, userId=request.app_user.email,
        )
    except ExamAttempt.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)

    if attempt.status == ExamAttempt.STATUS_SUBMITTED:
        return JsonResponse({'ok': False, 'expired': True, 'secondsLeft': 0})

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return HttpResponseBadRequest('Invalid JSON')

    answers = payload.get('answers', {})
    if not isinstance(answers, dict):
        return HttpResponseBadRequest('Invalid payload')

    expired = attempt.is_expired()
    if expired:
        # Czas minął — domknij i nie przyjmuj już nic nowego.
        attempt.submit()
        return JsonResponse({'ok': False, 'expired': True, 'secondsLeft': 0})

    attempt.answers = answers
    attempt.save(update_fields=['answers'])
    return JsonResponse({
        'ok': True, 'expired': False, 'secondsLeft': attempt.seconds_left(),
    })


@require_POST
@session_login_required
def exam_submit(request, attempt_id):
    """Jawne zakończenie egzaminu (przycisk 'Zakończ' lub auto-submit JS)."""
    try:
        attempt = ExamAttempt.objects.get(
            pk=attempt_id, userId=request.app_user.email,
        )
    except ExamAttempt.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)

    attempt.submit()
    return JsonResponse({
        'ok': True,
        'redirect': reverse('exam_result', args=[attempt.id]),
    })


@session_login_required
def exam_result(request, attempt_id):
    """Wynik symulacji egzaminu."""
    attempt = get_object_or_404(
        ExamAttempt, pk=attempt_id, userId=request.app_user.email,
    )
    if attempt.status != ExamAttempt.STATUS_SUBMITTED:
        attempt.submit()

    chart_data = json.dumps([
        {'area': area, 'score': score}
        for area, score in sorted((attempt.areaScores or {}).items())
    ])
    position = RankingService().getUserPosition(request.app_user.email)

    return render(request, 'ExtLearnerUJ/exam/result.html', {
        'attempt': attempt,
        'chart_data': chart_data,
        'position': position,
    })


# ============================================================
# Sprint 3 — ranking / gamifikacja (FR-07)
# ============================================================
@session_login_required
def ranking(request):
    """Top 10 studentów wg punktów + pozycja zalogowanego (FR-07)."""
    top = RankingService().getStudentRanking(top_n=10)
    my_position = RankingService().getUserPosition(request.app_user.email)
    my_stats = UserStats.objects.filter(userId=request.app_user.email).first()
    return render(request, 'ExtLearnerUJ/ranking.html', {
        'ranking': top,
        'my_position': my_position,
        'my_points': my_stats.points if my_stats else 0,
    })


# ============================================================
# Sprint 3 — statystyki nauki + raport PDF (UC15)
# ============================================================
@session_login_required
def my_stats(request):
    """Strona statystyk nauki studenta."""
    stats = request.app_user.viewStats()
    area_scores = json.dumps([
        {'area': a, 'score': s}
        for a, s in sorted((stats.get('last_area_scores') or {}).items())
    ])
    return render(request, 'ExtLearnerUJ/stats/my_stats.html', {
        'stats': stats,
        'area_scores': area_scores,
    })


@session_login_required
def learning_report_pdf(request):
    """UC15: pobranie raportu nauki w formacie PDF."""
    pdf_bytes = request.app_user.downloadLearningReport()
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        'attachment; filename="raport-nauki-extlearneruj.pdf"'
    )
    return response


# ============================================================
# Sprint 3 — wniosek o rolę moderatora (FR-12 / FR-02)
# ============================================================
@session_login_required
@role_required(Student)
def apply_moderator(request):
    """Student składa wniosek o rolę moderatora. Wniosek obejmuje test
    kwalifikacyjny — wynik poniżej progu odrzuca wniosek automatycznie
    (administrator nie jest angażowany)."""
    from .moderator_test import QUESTIONS, PASS_THRESHOLD, grade_answers

    existing = ModeratorApplication.objects.filter(
        candidateId=request.app_user.email,
    ).order_by('-createdAt').first()

    # Jeśli jest aktywny (PENDING) wniosek — pokaż jego status, nie pozwól
    # składać kolejnego.
    pending = existing if (existing and existing.status == 'PENDING') else None

    if request.method == 'POST' and pending is None:
        form = ModeratorApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            cert_path = ''
            cert = form.cleaned_data.get('certificate')
            if cert:
                att = FileAttachment()
                if att.upload(cert):
                    cert_path = att.filePath

            score = grade_answers(request.POST)
            application = request.app_user.applyForModerator(
                motivation=form.cleaned_data['motivation'],
                certificatePath=cert_path,
                testScore=score,
            )
            if application.status == ModeratorApplication.STATUS_REJECTED:
                messages.error(
                    request,
                    f'Wynik testu kwalifikacyjnego: {score}%. Próg to '
                    f'{PASS_THRESHOLD:.0f}% — wniosek został odrzucony '
                    f'automatycznie. Możesz spróbować ponownie.'
                )
            else:
                messages.success(
                    request,
                    f'Wynik testu: {score}%. Wniosek wysłany — administrator '
                    f'rozpatrzy go wkrótce.'
                )
            return redirect('apply_moderator')
    else:
        form = ModeratorApplicationForm()

    return render(request, 'ExtLearnerUJ/moderator/apply.html', {
        'form': form, 'pending': pending, 'last_application': existing,
        'test_questions': QUESTIONS, 'pass_threshold': PASS_THRESHOLD,
    })


# ============================================================
# Sprint 3 — panel finansowy moderatora (FR-14)
# ============================================================
@session_login_required
@role_required(Moderator, Admin)
def moderator_earnings(request):
    """Zarobki moderatora + zlecanie wypłaty (FR-14)."""
    stats = request.app_user.viewModeratorStats()
    return render(request, 'ExtLearnerUJ/moderator/earnings.html', {
        'stats': stats,
    })


@require_POST
@session_login_required
@role_required(Moderator, Admin)
def moderator_request_payout(request):
    """Zlecenie wypłaty dostępnego salda (FR-14)."""
    payout = request.app_user.requestPayout()
    if payout is None:
        messages.error(request, 'Brak środków do wypłaty.')
    else:
        messages.success(
            request,
            f'Zlecono wypłatę {payout.amount:.2f} zł. '
            f'Faktura: {payout.invoiceNumber}.'
        )
    return redirect('moderator_earnings')


# ============================================================
# Sprint 3 — admin: wnioski moderatorskie i zarządzanie rolami (FR-12)
# ============================================================
@session_login_required
@role_required(Admin)
def admin_applications(request):
    """Lista wniosków o rolę moderatora (FR-12)."""
    applications = request.app_user.reviewModeratorApplications()
    # Wzbogać o dane kandydata
    rows = []
    for app in applications:
        user = User.objects.filter(email=app.candidateId).first()
        rows.append({'application': app, 'user': user})
    return render(request, 'ExtLearnerUJ/admin_panel/applications.html', {
        'rows': rows,
    })


@session_login_required
@role_required(Admin)
def admin_review_application(request, application_id):
    """Rozpatrzenie wniosku o rolę moderatora (FR-12)."""
    application = get_object_or_404(ModeratorApplication, pk=application_id)
    candidate = User.objects.filter(email=application.candidateId).first()

    if request.method == 'POST' and application.status == 'PENDING':
        form = ReviewApplicationForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['decision'] == 'ACCEPT':
                request.app_user.acceptCandidate(application.id)
                messages.success(
                    request,
                    f'Wniosek zaakceptowany — {application.candidateId} '
                    f'jest teraz moderatorem.'
                )
            else:
                request.app_user.rejectCandidate(
                    application.id, reason=form.cleaned_data.get('comment', ''),
                )
                messages.success(request, 'Wniosek odrzucony.')
            return redirect('admin_applications')
    else:
        form = ReviewApplicationForm()

    return render(request, 'ExtLearnerUJ/admin_panel/review_application.html', {
        'application': application, 'candidate': candidate, 'form': form,
    })


@require_POST
@session_login_required
@role_required(Admin)
def admin_revoke_moderator(request, user_email):
    """Odebranie uprawnień moderatora (FR-12)."""
    if request.app_user.revokeModerator(user_email, reason='Decyzja administratora'):
        messages.success(request, f'Cofnięto uprawnienia moderatora: {user_email}.')
    else:
        messages.error(request, 'Nie udało się cofnąć uprawnień (czy to moderator?).')
    return redirect('admin_user_detail', user_email=user_email)
