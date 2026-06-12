"""
Test obciążeniowy (NFR-08) — symulacja nocy przed egzaminem.

Symuluje N jednoczesnych użytkowników uderzających w wybrany endpoint i mierzy
przepustowość oraz czasy odpowiedzi (p50/p95/max). Kryterium akceptacji NFR-08:
system zachowuje responsywność przy 50 jednoczesnych użytkownikach.

Uruchomienie (serwer musi działać osobno: `python manage.py runserver`):
    python manage.py loadtest --users 50 --requests 20
    python manage.py loadtest --url http://127.0.0.1:8000/healthz/ --users 50

Świadomie używamy tylko biblioteki standardowej (urllib + threading) — bez
dodatkowych zależności (locust itp.), żeby działało na darmowym hostingu i w CI.
"""
import threading
import time
import urllib.request
from statistics import median

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Prosty test obciążeniowy (NFR-08) — N równoległych użytkowników.'

    def add_arguments(self, parser):
        parser.add_argument('--url', default='http://127.0.0.1:8000/healthz/',
                            help='Endpoint do obciążenia (domyślnie /healthz/).')
        parser.add_argument('--users', type=int, default=50,
                            help='Liczba jednoczesnych użytkowników (wątków).')
        parser.add_argument('--requests', type=int, default=10,
                            help='Liczba żądań na użytkownika.')
        parser.add_argument('--timeout', type=float, default=10.0,
                            help='Timeout pojedynczego żądania (s).')

    def handle(self, *args, **opts):
        url = opts['url']
        users = opts['users']
        per_user = opts['requests']
        timeout = opts['timeout']
        total = users * per_user

        self.stdout.write(self.style.NOTICE(
            f'Load test: {users} użytkowników × {per_user} żądań = {total} → {url}'
        ))

        latencies = []
        errors = []
        lock = threading.Lock()

        def worker(worker_id):
            for _ in range(per_user):
                start = time.perf_counter()
                try:
                    with urllib.request.urlopen(url, timeout=timeout) as resp:
                        resp.read()
                        code = resp.getcode()
                    elapsed = time.perf_counter() - start
                    with lock:
                        latencies.append(elapsed)
                        if code >= 400:
                            errors.append(f'HTTP {code}')
                except Exception as exc:  # noqa: BLE001
                    with lock:
                        errors.append(str(exc))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(users)]
        wall_start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        wall = time.perf_counter() - wall_start

        ok = len(latencies)
        fail = len(errors)
        rps = ok / wall if wall > 0 else 0.0

        self.stdout.write('')
        self.stdout.write(f'  Czas całkowity:     {wall:.2f} s')
        self.stdout.write(f'  Udane żądania:      {ok}/{total}')
        self.stdout.write(f'  Błędy:              {fail}')
        self.stdout.write(f'  Przepustowość:      {rps:.1f} req/s')
        if latencies:
            latencies.sort()
            p95 = latencies[int(len(latencies) * 0.95) - 1]
            self.stdout.write(f'  Czas odpowiedzi:    '
                              f'p50={median(latencies)*1000:.0f} ms · '
                              f'p95={p95*1000:.0f} ms · '
                              f'max={max(latencies)*1000:.0f} ms')
        if errors[:5]:
            self.stdout.write(self.style.WARNING(
                '  Przykładowe błędy: ' + '; '.join(errors[:5])
            ))

        if fail == 0:
            self.stdout.write(self.style.SUCCESS(
                '  ✓ NFR-08: brak błędów przy zadanym obciążeniu.'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                '  ✗ Wystąpiły błędy — sprawdź logi serwera.'
            ))
