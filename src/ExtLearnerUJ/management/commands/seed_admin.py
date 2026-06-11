"""
Management command: tworzy startowe konto administratora.

Uruchomienie:
    python manage.py seed_admin

Admin nie rejestruje się przez formularz (rejestracja zawsze tworzy Studenta),
więc konto administracyjne zakładamy seedem. Dane logowania:
    e-mail:  admin@uj.edu.pl
    hasło:   AdminHaslo123
Zmień hasło po pierwszym zalogowaniu (funkcja „Nie pamiętam hasła").
"""
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from ExtLearnerUJ.models import Admin, User


ADMIN_EMAIL = 'admin@uj.edu.pl'
ADMIN_PASSWORD = 'AdminHaslo123'
ADMIN_NAME = 'Maria Admin'


class Command(BaseCommand):
    help = 'Seeds the initial administrator account.'

    def handle(self, *args, **options):
        if User.objects.filter(email__iexact=ADMIN_EMAIL).exists():
            self.stdout.write(self.style.WARNING(
                f'Konto {ADMIN_EMAIL} już istnieje — pomijam seeding.'
            ))
            return

        Admin.objects.create(
            email=ADMIN_EMAIL,
            password=make_password(ADMIN_PASSWORD),
            name=ADMIN_NAME,
            status=User.STATUS_ACTIVE,
            emailVerified=True,
        )
        self.stdout.write(self.style.SUCCESS(
            f'Utworzono konto administratora: {ADMIN_EMAIL} / {ADMIN_PASSWORD}'
        ))
