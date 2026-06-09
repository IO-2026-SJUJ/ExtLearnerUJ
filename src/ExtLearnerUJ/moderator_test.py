"""
Test kwalifikacyjny dla kandydatów na moderatora.

Kandydat wypełnia go przy składaniu wniosku. Wynik poniżej PASS_THRESHOLD (%)
oznacza automatyczne odrzucenie wniosku — administrator nie jest angażowany.
Pytania weryfikują znajomość angielskiego na poziomie ~B2+ (taki materiał
moderator będzie oceniać).
"""

PASS_THRESHOLD = 50.0

# Każde pytanie: id (stabilny klucz pola formularza), treść, opcje, indeks poprawnej.
QUESTIONS = [
    {
        'id': 'q1',
        'text': 'Choose the correct sentence:',
        'options': [
            'If I would have known, I would come earlier.',
            'If I had known, I would have come earlier.',
            'If I knew, I would have came earlier.',
            'If I have known, I came earlier.',
        ],
        'correct': 1,
    },
    {
        'id': 'q2',
        'text': '"She ___ the report by the time the meeting started."',
        'options': ['finished', 'has finished', 'had finished', 'was finishing'],
        'correct': 2,
    },
    {
        'id': 'q3',
        'text': 'Which word is closest in meaning to "meticulous"?',
        'options': ['careless', 'thorough', 'rapid', 'reluctant'],
        'correct': 1,
    },
    {
        'id': 'q4',
        'text': '"Hardly ___ the house when it started to rain."',
        'options': [
            'I had left', 'had I left', 'I left', 'did I leave',
        ],
        'correct': 1,
    },
    {
        'id': 'q5',
        'text': 'Choose the correctly punctuated sentence:',
        'options': [
            'The students, who passed the exam were happy.',
            'The students who passed the exam, were happy.',
            'The students who passed the exam were happy.',
            'The students, who passed, the exam were happy.',
        ],
        'correct': 2,
    },
    {
        'id': 'q6',
        'text': '"I\'d rather you ___ smoke in here."',
        'options': ["don't", "didn't", "won't", "wouldn't"],
        'correct': 1,
    },
    {
        'id': 'q7',
        'text': 'Which sentence uses the passive voice correctly?',
        'options': [
            'The essay was wrote by a student.',
            'The essay has been written by a student.',
            'The essay has wrote by a student.',
            'The essay was being write by a student.',
        ],
        'correct': 1,
    },
    {
        'id': 'q8',
        'text': '"Despite ___ hard, she failed the exam."',
        'options': ['she studied', 'of studying', 'studying', 'to study'],
        'correct': 2,
    },
]


def grade_answers(post_data) -> float:
    """Liczy wynik (%) na podstawie danych POST formularza.
    Brak odpowiedzi na pytanie liczy się jako odpowiedź błędna."""
    if not QUESTIONS:
        return 0.0
    correct = 0
    for q in QUESTIONS:
        raw = post_data.get(f"test_{q['id']}", '')
        try:
            if int(raw) == q['correct']:
                correct += 1
        except (TypeError, ValueError):
            pass
    return round(100.0 * correct / len(QUESTIONS), 1)
