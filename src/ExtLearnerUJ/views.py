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
<<<<<<< HEAD
from .forms import RegisterForm, LoginForm, VerifyEmailForm
from .models import (
    User, Student, Session, EmailVerificationToken,
    Material, DiagnosticTest, DiagnosticResult,
=======
from .forms import (
    RegisterForm, LoginForm, VerifyEmailForm,
    MaterialForm, ReportForm, VerifyMaterialForm,
    WorkForm, WorkReviewForm, AdminBlockUserForm, ReviewReportForm,
)
from .models import (
    User, Student, Moderator, Admin, Session, EmailVerificationToken,
    Material, DiagnosticTest, DiagnosticResult,
    Vote, Notification, MaterialVerification, Report, Comment,
    Work, Package, PaymentTransaction, WorkReview, ErrorMark, FileAttachment,
>>>>>>> sprint-2
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
<<<<<<< HEAD
    return render(request, 'ExtLearnerUJ/materials/detail.html', {
        'material': material,
=======
    # Czy aktualny user już głosował?
    user_voted = Vote.objects.filter(
        userId=request.app_user.email, materialId=str(material_id)
    ).exists()
    vote_count = Vote.objects.filter(materialId=str(material_id)).count()
    return render(request, 'ExtLearnerUJ/materials/detail.html', {
        'material': material,
        'user_voted': user_voted,
        'vote_count': vote_count,
>>>>>>> sprint-2
    })


# ============================================================
<<<<<<< HEAD
=======
# Sprint 2 — dodawanie materiałów (FR-08)
# ============================================================
@session_login_required
@role_required(Student)
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
    if not isinstance(request.app_user, Student):
        return JsonResponse({'error': 'Tylko studenci mogą głosować'}, status=403)

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
    return render(request, 'ExtLearnerUJ/notifications/list.html', {
        'notifications': notifications,
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


# ============================================================
>>>>>>> sprint-2
# Healthcheck (przydaje się w CI)
# ============================================================
def healthcheck(request):
    return JsonResponse({'status': 'ok'})
<<<<<<< HEAD
=======


# ============================================================
# Sprint 2 · tydzień 2 — Prace pisemne (FR-15, UC19/UC20/UC21)
# ============================================================
@session_login_required
@role_required(Student)
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
@role_required(Student)
def work_payment(request, work_id):
    """Ekran płatności (mock). Po kliknięciu 'Zapłać' transakcja jest
    przetwarzana przez mock bramki i praca przechodzi w status PAID."""
    work = get_object_or_404(Work, pk=work_id, studentId=request.app_user.email)

    if work.status != Work.STATUS_PENDING_PAYMENT:
        messages.info(request, 'Ta praca jest już opłacona.')
        return redirect('work_detail', work_id=work.id)

    package = get_object_or_404(Package, pk=work.packageId)

    if request.method == 'POST':
        method = request.POST.get('method', PaymentTransaction.METHOD_BLIK)

        tx = PaymentTransaction.objects.create(
            workId=str(work.id),
            userId=request.app_user.email,
            amount=package.price,
            method=method,
        )
        success = tx.process()  # mock — zawsze sukces

        if success:
            messages.success(
                request,
                f'Płatność przyjęta ({package.price} zł). '
                f'Praca czeka na moderatora — czas realizacji: 48h.'
            )
            return redirect('work_detail', work_id=work.id)
        else:
            messages.error(
                request,
                'Płatność nie powiodła się. Spróbuj ponownie lub zmień metodę.'
            )

    return render(request, 'ExtLearnerUJ/works/payment.html', {
        'work': work, 'package': package,
    })


@session_login_required
@role_required(Student)
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

    return render(request, 'ExtLearnerUJ/works/detail.html', {
        'work': work, 'package': package, 'review': review,
        'error_marks': error_marks,
    })


@session_login_required
@role_required(Student)
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
    return render(request, 'ExtLearnerUJ/moderator/works_queue.html', {
        'works': works,
    })


@require_POST
@session_login_required
@role_required(Moderator, Admin)
def moderator_reserve_work(request, work_id):
    """Moderator rezerwuje pracę do sprawdzenia (UC39)."""
    if isinstance(request.app_user, Moderator):
        success = request.app_user.reserveWork(work_id)
    else:
        # Admin — tak samo, ale bezpośrednio
        try:
            work = Work.objects.get(pk=work_id)
            success = work.assignModerator(request.app_user.email)
        except Work.DoesNotExist:
            success = False

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
    if report.targetType == Report.TARGET_MATERIAL:
        try:
            target = Material.objects.get(pk=report.targetId)
        except Material.DoesNotExist:
            target = None
    elif report.targetType == Report.TARGET_USER:
        try:
            target = User.objects.get(email=report.targetId)
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
        'report': report, 'target': target, 'form': form,
    })


@session_login_required
@role_required(Admin)
def admin_users_list(request):
    """Lista wszystkich użytkowników (UC48)."""
    users = User.objects.all().order_by('-registrationDate')
    return render(request, 'ExtLearnerUJ/admin_panel/users_list.html', {
        'users': users,
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
            )
            messages.success(
                request,
                f'Konto {user.email} zostało zablokowane.'
            )
            return redirect('admin_user_detail', user_email=user.email)
    else:
        form = AdminBlockUserForm()

    return render(request, 'ExtLearnerUJ/admin_panel/user_detail.html', {
        'target_user': user, 'materials': materials,
        'reports_made': reports_made, 'reports_against': reports_against,
        'form': form,
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
>>>>>>> sprint-2
