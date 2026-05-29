"""
Formularze Django. Walidacja odbywa się tu, widoki tylko orkiestrują
(Single Responsibility Principle).
"""
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User


class RegisterForm(forms.Form):
    name = forms.CharField(
        max_length=100, min_length=2,
        label='Imię i nazwisko',
        widget=forms.TextInput(attrs={'autocomplete': 'name', 'autofocus': True}),
    )
    email = forms.EmailField(
        label='Adres e-mail',
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )
    password = forms.CharField(
        min_length=8,
        label='Hasło',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='Minimum 8 znaków, nie samo z cyfr.',
    )
    password_confirm = forms.CharField(
        label='Powtórz hasło',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Konto z tym adresem e-mail już istnieje.')
        return email

    def clean_password(self):
        pw = self.cleaned_data['password']
        try:
            validate_password(pw)
        except ValidationError as e:
            raise ValidationError(list(e.messages))
        return pw

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') and cleaned.get('password_confirm'):
            if cleaned['password'] != cleaned['password_confirm']:
                self.add_error('password_confirm', 'Hasła muszą być takie same.')
        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Adres e-mail',
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'autofocus': True}),
    )
    password = forms.CharField(
        label='Hasło',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )


class VerifyEmailForm(forms.Form):
    code = forms.CharField(
        min_length=6, max_length=6,
        label='Kod weryfikacyjny',
        widget=forms.TextInput(attrs={
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'pattern': '[0-9]{6}',
            'autofocus': True,
        }),
        help_text='6-cyfrowy kod wysłany na Twój e-mail.',
    )

    def clean_code(self):
        code = self.cleaned_data['code'].strip()
        if not code.isdigit():
            raise ValidationError('Kod musi składać się z cyfr.')
        return code


# ============================================================
# Sprint 2 — materiały, zgłoszenia, weryfikacja
# ============================================================
MATERIAL_CATEGORIES = [
    ('grammar', 'Gramatyka'),
    ('reading', 'Czytanie'),
    ('listening', 'Słuchanie'),
    ('vocabulary', 'Słownictwo'),
]

ALLOWED_UPLOAD_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/jpeg',
    'image/png',
    'text/plain',
}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class MaterialForm(forms.Form):
    """Formularz dodawania materiału przez studenta (FR-08)."""
    title = forms.CharField(
        min_length=3, max_length=255,
        label='Tytuł materiału',
        widget=forms.TextInput(attrs={'autofocus': True}),
    )
    category = forms.ChoiceField(
        choices=MATERIAL_CATEGORIES,
        label='Kategoria',
    )
    content = forms.CharField(
        min_length=20,
        label='Opis / treść',
        widget=forms.Textarea(attrs={'rows': 8}),
        help_text='Przynajmniej 20 znaków. Opisz czego dotyczy materiał, '
                  'co student z niego skorzysta.',
    )
    attachment = forms.FileField(
        label='Plik (opcjonalnie)',
        required=False,
        help_text=f'PDF, DOCX, TXT, JPG lub PNG. Maksymalnie '
                  f'{MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB.',
    )

    def clean_attachment(self):
        f = self.cleaned_data.get('attachment')
        if f is None:
            return None
        if f.size > MAX_UPLOAD_SIZE_BYTES:
            raise ValidationError(
                f'Plik jest za duży ({f.size // 1024} KB). '
                f'Maksymalnie {MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB.'
            )
        if f.content_type not in ALLOWED_UPLOAD_TYPES:
            raise ValidationError(
                f'Niedozwolony typ pliku: {f.content_type}. '
                'Akceptujemy: PDF, DOCX, TXT, JPG, PNG.'
            )
        return f


class ReportForm(forms.Form):
    """Zgłoszenie materiału/usera/komentarza (FR-13)."""
    reason = forms.CharField(
        min_length=10, max_length=1000,
        label='Powód zgłoszenia',
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text='Opisz dokładnie, co jest nie tak (min. 10 znaków).',
    )


class VerifyMaterialForm(forms.Form):
    """Decyzja moderatora o materiale (UC31)."""
    DECISION_CHOICES = [
        ('ACCEPTED', 'Zaakceptuj'),
        ('REJECTED', 'Odrzuć'),
        ('NEEDS_REVISION', 'Wyślij do poprawy'),
    ]

    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect,
        label='Decyzja',
    )
    comment = forms.CharField(
        required=False,
        max_length=2000,
        label='Komentarz dla autora (opcjonalny)',
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text='Szczególnie ważny przy odrzuceniu lub wysłaniu do poprawy.',
    )

    def clean(self):
        cleaned = super().clean()
        # Komentarz obowiązkowy przy REJECTED/NEEDS_REVISION
        if cleaned.get('decision') in ('REJECTED', 'NEEDS_REVISION'):
            if not cleaned.get('comment', '').strip():
                self.add_error(
                    'comment',
                    'Komentarz wymagany przy odrzuceniu lub wysłaniu do poprawy.'
                )
        return cleaned


# ============================================================
# Sprint 2 · tydzień 2 — prace pisemne, płatności, edytor, admin
# ============================================================
WORK_ALLOWED_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
}


class WorkForm(forms.Form):
    """Formularz wysłania pracy pisemnej do sprawdzenia (FR-15, UC19)."""
    title = forms.CharField(
        min_length=3, max_length=255,
        label='Tytuł pracy',
        widget=forms.TextInput(attrs={'autofocus': True,
                                      'placeholder': 'np. Opinion essay on free education'}),
    )
    description = forms.CharField(
        label='Treść pracy',
        widget=forms.Textarea(attrs={'rows': 14,
                                     'placeholder': 'Wklej treść pracy tutaj — '
                                                    'albo zostaw puste i załącz plik poniżej.'}),
        required=False,
    )
    attachment = forms.FileField(
        label='Plik z pracą (opcjonalnie)',
        required=False,
        help_text='PDF, DOCX lub TXT. Max 10 MB.',
    )
    package = forms.ModelChoiceField(
        queryset=None,  # ustawiamy w __init__
        label='Wybierz pakiet sprawdzenia',
        widget=forms.RadioSelect,
        empty_label=None,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import tu zamiast u góry, żeby uniknąć cyrkularności
        from .models import Package
        self.fields['package'].queryset = Package.objects.all()

    def clean_attachment(self):
        f = self.cleaned_data.get('attachment')
        if f is None:
            return None
        if f.size > MAX_UPLOAD_SIZE_BYTES:
            raise ValidationError(
                f'Plik jest za duży ({f.size // 1024} KB). '
                f'Maksymalnie {MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB.'
            )
        if f.content_type not in WORK_ALLOWED_TYPES:
            raise ValidationError(
                f'Niedozwolony typ pliku: {f.content_type}. '
                'Akceptujemy: PDF, DOCX, TXT.'
            )
        return f

    def clean(self):
        cleaned = super().clean()
        # Musi być treść ALBO plik
        if not cleaned.get('description', '').strip() and not cleaned.get('attachment'):
            raise ValidationError(
                'Podaj treść pracy lub załącz plik — inaczej moderator '
                'nie będzie miał czego sprawdzać.'
            )
        return cleaned


CEFR_LEVELS = [
    ('', '— wybierz —'),
    ('A1', 'A1'),
    ('A2', 'A2'),
    ('B1', 'B1'),
    ('B2', 'B2'),
    ('B2+', 'B2+'),
    ('C1', 'C1'),
    ('C2', 'C2'),
]


class WorkReviewForm(forms.Form):
    """Formularz oceny pracy przez moderatora (FR-10, UC40)."""
    grade = forms.ChoiceField(
        choices=CEFR_LEVELS,
        label='Ocena CEFR',
    )
    generalComment = forms.CharField(
        min_length=20,
        max_length=5000,
        label='Komentarz ogólny',
        widget=forms.Textarea(attrs={'rows': 8,
                                     'placeholder': 'Mocne strony pracy, '
                                                    'obszary do poprawy, ogólne wrażenie...'}),
    )


class AdminBlockUserForm(forms.Form):
    """Blokada konta użytkownika przez admina (FR-11, UC48)."""
    DURATION_CHOICES = [
        ('1', '1 dzień'),
        ('7', '7 dni'),
        ('30', '30 dni'),
        ('permanent', 'Na stałe'),
    ]

    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        widget=forms.RadioSelect,
        label='Czas blokady',
    )
    reason = forms.CharField(
        min_length=10, max_length=500,
        label='Powód (widoczny dla admina, nie wysyłany do usera)',
        widget=forms.Textarea(attrs={'rows': 3}),
    )


class ReviewReportForm(forms.Form):
    """Rozpatrzenie zgłoszenia przez admina (UC47)."""
    DECISION_CHOICES = [
        ('RESOLVED', 'Uznaj za zasadne'),
        ('DISMISSED', 'Odrzuć'),
    ]

    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect,
        label='Decyzja',
    )
    comment = forms.CharField(
        required=False,
        max_length=1000,
        label='Notatka wewnętrzna (opcjonalnie)',
        widget=forms.Textarea(attrs={'rows': 3}),
    )
