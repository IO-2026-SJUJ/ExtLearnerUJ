"""
Management command: seeds the timed exam simulation (FR-06).

Uruchomienie:
    python manage.py seed_exam

Tworzy Test typu EXAM z limitem czasu (durationMinutes) i zestawem pytań
B2+ w czterech obszarach. To NIE są prawdziwe arkusze UJ (O-03/O-04) — to
przykładowe pytania demonstrujące mechanizm twardego timera i oceniania.
"""
from django.core.management.base import BaseCommand

from ExtLearnerUJ.models import Test, Question


EXAM_DURATION_MINUTES = 30

QUESTIONS_DATA = [
    # ---- Grammar ----
    {'area': 'grammar', 'text': 'By next year, she ___ here for a decade.',
     'options': ['will work', 'will have worked', 'works', 'worked'],
     'correct': 'will have worked'},
    {'area': 'grammar', 'text': 'Hardly ___ when the phone rang.',
     'options': ['I had sat down', 'had I sat down', 'I sat down', 'did I sit down'],
     'correct': 'had I sat down'},
    {'area': 'grammar', 'text': 'It is high time we ___ about it.',
     'options': ['do something', 'did something', 'have done something', 'will do something'],
     'correct': 'did something'},
    {'area': 'grammar', 'text': 'The proposal, ___ was rejected, took months to prepare.',
     'options': ['which', 'that', 'what', 'whose'], 'correct': 'which'},
    {'area': 'grammar', 'text': 'I would rather you ___ smoke in here.',
     'options': ["didn't", "don't", "won't", "wouldn't"], 'correct': "didn't"},

    # ---- Reading ----
    {'area': 'reading', 'text': '"To curtail spending" means to:',
     'options': ['increase it', 'reduce it', 'track it', 'hide it'], 'correct': 'reduce it'},
    {'area': 'reading', 'text': 'A "candid" remark is one that is:',
     'options': ['dishonest', 'frank and honest', 'unclear', 'rude'],
     'correct': 'frank and honest'},
    {'area': 'reading', 'text': '"Ostensibly" most nearly means:',
     'options': ['secretly', 'apparently', 'rarely', 'eventually'], 'correct': 'apparently'},
    {'area': 'reading', 'text': 'Something "innocuous" is:',
     'options': ['harmless', 'dangerous', 'expensive', 'illegal'], 'correct': 'harmless'},
    {'area': 'reading', 'text': 'To "scrutinise" a document is to:',
     'options': ['ignore it', 'sign it', 'examine it closely', 'copy it'],
     'correct': 'examine it closely'},

    # ---- Listening ----
    {'area': 'listening', 'text': '"Bear with me" asked of you means:',
     'options': ['be patient', 'help me lift', 'agree with me', 'leave now'],
     'correct': 'be patient'},
    {'area': 'listening', 'text': '"Let me get back to you" means the speaker will:',
     'options': ['return physically', 'reply later', 'refuse', 'repeat'],
     'correct': 'reply later'},
    {'area': 'listening', 'text': '"Speak up" means:',
     'options': ['talk louder', 'stop talking', 'talk faster', 'change topic'],
     'correct': 'talk louder'},
    {'area': 'listening', 'text': '"That rings a bell" means it:',
     'options': ['is annoying', 'sounds familiar', 'is an alarm', 'is wrong'],
     'correct': 'sounds familiar'},
    {'area': 'listening', 'text': '"Run that by me again" is a request to:',
     'options': ['hurry', 'repeat / explain again', 'leave', 'drive'],
     'correct': 'repeat / explain again'},

    # ---- Vocabulary ----
    {'area': 'vocabulary', 'text': 'The opposite of "tentative" is:',
     'options': ['hesitant', 'definite', 'temporary', 'shy'], 'correct': 'definite'},
    {'area': 'vocabulary', 'text': '"Lucid" writing is:',
     'options': ['clear', 'confusing', 'boring', 'long'], 'correct': 'clear'},
    {'area': 'vocabulary', 'text': 'To "alleviate" pain is to:',
     'options': ['worsen it', 'relieve it', 'describe it', 'cause it'],
     'correct': 'relieve it'},
    {'area': 'vocabulary', 'text': 'A "prudent" decision is:',
     'options': ['reckless', 'sensible and careful', 'sudden', 'expensive'],
     'correct': 'sensible and careful'},
    {'area': 'vocabulary', 'text': '"Inevitable" means:',
     'options': ['avoidable', 'unavoidable', 'unlikely', 'optional'],
     'correct': 'unavoidable'},
]


class Command(BaseCommand):
    help = 'Seeds the timed exam simulation (FR-06).'

    def handle(self, *args, **options):
        if Test.objects.filter(type=Test.TYPE_EXAM).exists():
            self.stdout.write(self.style.WARNING(
                'Symulacja egzaminu już istnieje — pomijam seeding.'
            ))
            return

        test = Test.objects.create(
            title='Symulacja egzaminu B2+ (UJ)',
            type=Test.TYPE_EXAM,
            durationMinutes=EXAM_DURATION_MINUTES,
        )

        for q in QUESTIONS_DATA:
            Question.objects.create(
                test=test,
                text=q['text'],
                qType=Question.QTYPE_SINGLE,
                options=q['options'],
                correctAnswer=q['correct'],
                area=q['area'],
                points=1,
            )

        self.stdout.write(self.style.SUCCESS(
            f'Utworzono symulację egzaminu (id={test.id}) z {len(QUESTIONS_DATA)} '
            f'pytaniami, limit {EXAM_DURATION_MINUTES} min.'
        ))
