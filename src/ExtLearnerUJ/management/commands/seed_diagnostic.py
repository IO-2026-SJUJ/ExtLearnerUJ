"""
Management command: seeds the diagnostic test.

Uruchomienie:
    python manage.py seed_diagnostic

Tworzy DiagnosticTest z min. 20 pytaniami w 4 obszarach (grammar, reading,
listening, vocabulary) — wystarczająco, żeby FR-04 i FR-05 dało się pokazać.

Uwaga: to nie są "prawdziwe" pytania egzaminacyjne UJ (to mitygacja R6.3 —
do Sprintu 2 zespół pozyska materiały z British Council/BBC/Cambridge).
Tu są przykładowe pytania B2+ wystarczające do zademonstrowania flow.
"""
from django.core.management.base import BaseCommand

from ExtLearnerUJ.models import DiagnosticTest, Question


QUESTIONS_DATA = [
    # ---- Grammar ----
    {'area': 'grammar', 'text': 'If I ___ more time, I would learn another language.',
     'options': ['had', 'have', 'would have', 'am having'], 'correct': 'had'},
    {'area': 'grammar', 'text': 'She ___ working here since 2019.',
     'options': ['is', 'has been', 'was', 'had been'], 'correct': 'has been'},
    {'area': 'grammar', 'text': 'I wish I ___ how to drive.',
     'options': ['know', 'knew', 'had known', 'would know'], 'correct': 'knew'},
    {'area': 'grammar', 'text': 'The report ___ by the end of next week.',
     'options': ['will finish', 'will be finished', 'will have been finished',
                 'is finishing'], 'correct': 'will have been finished'},
    {'area': 'grammar', 'text': 'Not only ___ late, but he also forgot the documents.',
     'options': ['he was', 'was he', 'he had been', 'did he'],
     'correct': 'was he'},

    # ---- Reading (tu uproszczone — na prawdziwym teście byłyby dłuższe teksty) ----
    {'area': 'reading',
     'text': 'In formal writing, "notwithstanding" most closely means:',
     'options': ['despite', 'because of', 'before', 'instead of'], 'correct': 'despite'},
    {'area': 'reading',
     'text': '"The argument was specious" — what does "specious" mean?',
     'options': ['convincing and true', 'misleadingly plausible',
                 'overly complex', 'brief and weak'],
     'correct': 'misleadingly plausible'},
    {'area': 'reading',
     'text': 'Which is the best synonym for "mitigate"?',
     'options': ['aggravate', 'alleviate', 'accelerate', 'anticipate'],
     'correct': 'alleviate'},
    {'area': 'reading',
     'text': '"Ubiquitous" technology is best described as:',
     'options': ['rare', 'outdated', 'present everywhere', 'unreliable'],
     'correct': 'present everywhere'},
    {'area': 'reading',
     'text': 'A "cogent" argument is:',
     'options': ['weak and emotional', 'clear and convincing',
                 'long and repetitive', 'mysterious'],
     'correct': 'clear and convincing'},

    # ---- Listening (tu w formie tekstowej zdań do uzupełnienia — w Sprincie 2 dodajemy audio) ----
    {'area': 'listening',
     'text': 'Complete from context: "I couldn\'t ___ what she said — the line was breaking up."',
     'options': ['make on', 'make out', 'make up', 'make into'],
     'correct': 'make out'},
    {'area': 'listening',
     'text': '"Could you ___ that please? I didn\'t catch it."',
     'options': ['repeat up', 'repeat on', 'repeat', 'repeat over'],
     'correct': 'repeat'},
    {'area': 'listening',
     'text': 'In phone English, "hang on" means:',
     'options': ['end the call', 'wait a moment',
                 'call back later', 'speak louder'],
     'correct': 'wait a moment'},
    {'area': 'listening',
     'text': 'The expression "I beg your pardon?" is used when you:',
     'options': ['apologise for being late', 'ask someone to repeat',
                 'accept an invitation', 'refuse an offer'],
     'correct': 'ask someone to repeat'},
    {'area': 'listening',
     'text': '"Sorry, you\'re breaking up" most likely means:',
     'options': ['ending a relationship', 'poor phone reception',
                 'sad news', 'laughing'],
     'correct': 'poor phone reception'},

    # ---- Vocabulary ----
    {'area': 'vocabulary',
     'text': 'The opposite of "abundant" is:',
     'options': ['plentiful', 'scarce', 'enormous', 'common'],
     'correct': 'scarce'},
    {'area': 'vocabulary',
     'text': '"Meticulous" means:',
     'options': ['careless', 'extremely careful', 'tired', 'loud'],
     'correct': 'extremely careful'},
    {'area': 'vocabulary',
     'text': 'A "benevolent" person is:',
     'options': ['kind and generous', 'strict and cold',
                 'shy and quiet', 'angry and rude'],
     'correct': 'kind and generous'},
    {'area': 'vocabulary',
     'text': 'To "exacerbate" a problem is to:',
     'options': ['solve it', 'ignore it', 'make it worse', 'explain it'],
     'correct': 'make it worse'},
    {'area': 'vocabulary',
     'text': '"Pragmatic" most closely means:',
     'options': ['dreamy', 'practical', 'philosophical', 'emotional'],
     'correct': 'practical'},
]


class Command(BaseCommand):
    help = 'Seeds the diagnostic test with sample B2+ questions.'

    def handle(self, *args, **options):
        if DiagnosticTest.objects.exists():
            self.stdout.write(self.style.WARNING(
                'DiagnosticTest już istnieje — pomijam seeding. '
                'Użyj `python manage.py flush` aby wyczyścić bazę.'
            ))
            return

        test = DiagnosticTest.objects.create(
            title='Test diagnostyczny B2+ (UJ)',
            type='DIAGNOSTIC',
        )

        for q_data in QUESTIONS_DATA:
            Question.objects.create(
                test=test,
                text=q_data['text'],
                qType=Question.QTYPE_SINGLE,
                options=q_data['options'],
                correctAnswer=q_data['correct'],
                area=q_data['area'],
                points=1,
            )

        self.stdout.write(self.style.SUCCESS(
            f'Utworzono DiagnosticTest (id={test.id}) z {len(QUESTIONS_DATA)} pytaniami.'
        ))
