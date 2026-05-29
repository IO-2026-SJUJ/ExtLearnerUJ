"""Seed startowych pakietów sprawdzania prac pisemnych."""
from django.core.management.base import BaseCommand

from ExtLearnerUJ.models import Package


PACKAGES = [
    {
        'name': 'Podstawowy',
        'price': 15.0,
        'scope': 'Ocena CEFR + komentarz ogólny',
        'description': (
            'Moderator oceni Twoją pracę według skali CEFR (A1–C2) i napisze '
            'kilka zdań o mocnych i słabych stronach. Realizacja do 48h.'
        ),
    },
    {
        'name': 'Rozszerzony',
        'price': 25.0,
        'scope': 'Ocena CEFR + szczegółowe zaznaczenia błędów + komentarz',
        'description': (
            'Pełny feedback: kolorowe zaznaczenia błędów gramatycznych '
            '(czerwone), nienaturalnych sformułowań (żółte) oraz pochwał '
            '(zielone). Plus rozbudowany komentarz ogólny. Realizacja do 48h.'
        ),
    },
    {
        'name': 'Ekspresowy 24h',
        'price': 40.0,
        'scope': 'Jak Rozszerzony, ale z gwarancją do 24h',
        'description': (
            'Ten sam zakres co pakiet Rozszerzony, ale priorytetowo — '
            'praca trafia na początek kolejki i jest sprawdzana w ciągu 24h. '
            'Idealny tuż przed egzaminem.'
        ),
    },
]


class Command(BaseCommand):
    help = 'Seeds pricing packages for work reviews.'

    def handle(self, *args, **options):
        if Package.objects.exists():
            self.stdout.write(self.style.WARNING(
                'Pakiety już istnieją — pomijam seeding.'
            ))
            return

        for p in PACKAGES:
            Package.objects.create(**p)

        self.stdout.write(self.style.SUCCESS(
            f'Utworzono {len(PACKAGES)} pakietów.'
        ))
