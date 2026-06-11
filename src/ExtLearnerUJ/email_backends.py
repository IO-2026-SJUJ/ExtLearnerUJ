"""
Backend e-mail wysyłający wiadomości przez API Resend (HTTPS, port 443).

Używany w środowiskach, gdzie wychodzący SMTP (porty 25/465/587) jest
zablokowany — np. na darmowym planie Render. Aktywowany ustawieniem
RESEND_API_KEY; obsługuje standardowe send_mail() i EmailMessage(), więc
nie wymaga zmian w miejscach wysyłki.

Bez zewnętrznych zależności — korzysta z biblioteki standardowej (urllib).
"""
import json
import urllib.request
import urllib.error

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

RESEND_API_URL = 'https://api.resend.com/emails'


class ResendEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'RESEND_API_KEY', '') or ''

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        if not self.api_key:
            if not self.fail_silently:
                raise ValueError('RESEND_API_KEY nie jest ustawiony.')
            return 0

        sent = 0
        for message in email_messages:
            try:
                self._send_single(message)
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent

    def _send_single(self, message):
        payload = {
            'from': message.from_email,
            'to': list(message.to),
            'subject': message.subject,
            'text': message.body,
        }
        if message.cc:
            payload['cc'] = list(message.cc)
        if message.bcc:
            payload['bcc'] = list(message.bcc)
        if message.reply_to:
            payload['reply_to'] = list(message.reply_to)

        # Wersja HTML, jeśli dołączona jako alternatywa treści.
        for content, mimetype in getattr(message, 'alternatives', []) or []:
            if mimetype == 'text/html':
                payload['html'] = content
                break

        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(
            RESEND_API_URL,
            data=data,
            method='POST',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                response.read()
        except urllib.error.HTTPError as exc:
            # Wyciągnij komunikat błędu z odpowiedzi Resend (czytelniejszy log).
            detail = exc.read().decode('utf-8', 'replace')
            raise RuntimeError(f'Resend API {exc.code}: {detail}') from exc
