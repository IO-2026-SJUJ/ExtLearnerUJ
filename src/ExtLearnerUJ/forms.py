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
