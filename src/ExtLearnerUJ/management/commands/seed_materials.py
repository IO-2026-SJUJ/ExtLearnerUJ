"""
Seed kilku przykładowych materiałów — żeby lista nie była pusta
w dniu pierwszego uruchomienia. Sprint 2 doda właściwy flow dodawania.
"""
from django.core.management.base import BaseCommand

from ExtLearnerUJ.models import Material


SAMPLE_MATERIALS = [
    {'title': 'Present Perfect — zastosowanie w praktyce', 'category': 'grammar',
     'content': 'Kompendium zastosowań czasu Present Perfect z przykładami...',
     'verified': True, 'priority': 42},
    {'title': 'Phrasal verbs z "get"', 'category': 'vocabulary',
     'content': 'Najczęstsze czasowniki frazowe z "get"...',
     'verified': True, 'priority': 28},
    {'title': 'Reading comprehension — strategia', 'category': 'reading',
     'content': 'Jak skutecznie podejść do tekstów na egzaminie B2+...',
     'verified': True, 'priority': 19},
    {'title': 'Listening — job interviews', 'category': 'listening',
     'content': 'Scenariusze rozmów kwalifikacyjnych...',
     'verified': False, 'priority': 15},
    {'title': 'Conditional sentences — wszystkie typy', 'category': 'grammar',
     'content': 'Okresy warunkowe od zerowego do mieszanego...',
     'verified': False, 'priority': 7},
    {'title': 'Akademickie kolokacje', 'category': 'vocabulary',
     'content': 'Kolokacje przydatne w pracach pisemnych...',
     'verified': True, 'priority': 12},
]


class Command(BaseCommand):
    help = 'Seeds a few sample materials so the list is not empty on first run.'

    def handle(self, *args, **options):
        if Material.objects.exists():
            self.stdout.write(self.style.WARNING(
                'Materiały już istnieją — pomijam seeding.'
            ))
            return

        for m in SAMPLE_MATERIALS:
            Material.objects.create(
                title=m['title'],
                content=m['content'],
                category=m['category'],
                authorId='seed@extlearner.uj.edu.pl',
                status=Material.STATUS_VERIFIED if m['verified'] else Material.STATUS_PENDING,
                isVerified=m['verified'],
                priority=m['priority'],
            )

        self.stdout.write(self.style.SUCCESS(
            f'Utworzono {len(SAMPLE_MATERIALS)} przykładowych materiałów.'
        ))
