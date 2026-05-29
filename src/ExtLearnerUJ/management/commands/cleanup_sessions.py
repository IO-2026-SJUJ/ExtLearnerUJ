"""Sprząta wygasłe sesje. Uruchamiać z crona (w produkcji codziennie)."""
from django.core.management.base import BaseCommand
from django.utils import timezone

from ExtLearnerUJ.models import Session, EmailVerificationToken


class Command(BaseCommand):
    help = 'Usuwa wygasłe sesje i tokeny weryfikacyjne.'

    def handle(self, *args, **options):
        now = timezone.now()

        s_deleted, _ = Session.objects.filter(expiresAt__lt=now).delete()
        t_deleted, _ = EmailVerificationToken.objects.filter(expiresAt__lt=now).delete()

        self.stdout.write(self.style.SUCCESS(
            f'Usunięto {s_deleted} sesji i {t_deleted} tokenów.'
        ))
