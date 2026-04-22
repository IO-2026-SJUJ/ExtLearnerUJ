"""Testy Sprintu 1 — materiały (lista, filtry, szczegóły)."""
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse

from ExtLearnerUJ.models import User, EmailVerificationToken, Material


def _make_verified_student(email='mat@uj.edu.pl', password='SilneHaslo123'):
    user = User.register(email, password, 'Mat Student')
    token = EmailVerificationToken.objects.get(userId=email).token
    user.verifyEmail(token)
    return user


class MaterialsListTests(TestCase):
    def setUp(self):
        self.user = _make_verified_student()
        session = User.authenticate('mat@uj.edu.pl', 'SilneHaslo123')
        self.client = Client()
        self.client.cookies[settings.SESSION_COOKIE_NAME_APP] = session.token

        self.m1 = Material.objects.create(
            title='Grammar A', category='grammar', authorId='a@uj.edu.pl',
            status=Material.STATUS_VERIFIED, isVerified=True, priority=10,
        )
        self.m2 = Material.objects.create(
            title='Reading B', category='reading', authorId='a@uj.edu.pl',
            status=Material.STATUS_PENDING, isVerified=False, priority=5,
        )
        self.m3 = Material.objects.create(
            title='Grammar C', category='grammar', authorId='a@uj.edu.pl',
            status=Material.STATUS_VERIFIED, isVerified=True, priority=20,
        )

    def test_list_requires_login(self):
        anon = Client()
        response = anon.get(reverse('materials_list'))
        self.assertEqual(response.status_code, 302)

    def test_list_shows_all_materials_by_default(self):
        response = self.client.get(reverse('materials_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Grammar A')
        self.assertContains(response, 'Reading B')
        self.assertContains(response, 'Grammar C')

    def test_filter_by_category(self):
        response = self.client.get(reverse('materials_list'), {'category': 'grammar'})
        self.assertContains(response, 'Grammar A')
        self.assertContains(response, 'Grammar C')
        self.assertNotContains(response, 'Reading B')

    def test_filter_verified_only(self):
        response = self.client.get(reverse('materials_list'), {'status': 'verified'})
        self.assertContains(response, 'Grammar A')
        self.assertNotContains(response, 'Reading B')

    def test_filter_pending_only(self):
        response = self.client.get(reverse('materials_list'), {'status': 'pending'})
        self.assertContains(response, 'Reading B')
        self.assertNotContains(response, 'Grammar A')

    def test_ordering_by_priority_desc(self):
        """Materiały powinny być sortowane priorytetem malejąco
        (C:20 > A:10) — mitygacja R6.3 i wymaganie UC07+UC09."""
        response = self.client.get(reverse('materials_list'))
        content = response.content.decode('utf-8')
        self.assertLess(content.index('Grammar C'), content.index('Grammar A'))


class MaterialDetailTests(TestCase):
    def setUp(self):
        self.user = _make_verified_student()
        session = User.authenticate('mat@uj.edu.pl', 'SilneHaslo123')
        self.client = Client()
        self.client.cookies[settings.SESSION_COOKIE_NAME_APP] = session.token

        self.material = Material.objects.create(
            title='Treść testowa', content='Zawartość materiału.',
            category='grammar', authorId='a@uj.edu.pl',
            status=Material.STATUS_VERIFIED, isVerified=True,
        )

    def test_detail_accessible(self):
        response = self.client.get(
            reverse('material_detail', args=[self.material.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Treść testowa')
        self.assertContains(response, 'Zawartość materiału.')

    def test_nonexistent_material_returns_404(self):
        response = self.client.get(reverse('material_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)


class MaterialModelTests(TestCase):
    def test_increase_priority(self):
        m = Material.objects.create(
            title='X', authorId='a@uj.edu.pl', priority=5,
        )
        m.increasePriority()
        m.refresh_from_db()
        self.assertEqual(m.priority, 6)

    def test_create_with_class_method(self):
        m = Material.create({
            'title': 'Klasowy', 'content': 'tekst', 'authorId': 'a@uj.edu.pl',
            'category': 'grammar',
        })
        self.assertIsNotNone(m.id)
        self.assertEqual(m.status, Material.STATUS_PENDING)
        self.assertEqual(m.priority, 0)
        self.assertFalse(m.isVerified)
