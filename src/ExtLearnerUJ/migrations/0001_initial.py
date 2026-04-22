"""Migracja początkowa — Sprint 1.
Generowana ręcznie, spójna z models.py po fixach bugów."""
import django.db.models.deletion
from django.db import migrations, models

import ExtLearnerUJ.models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        # ===== User + role (multi-table inheritance) =====
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=255, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('password', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[
                    ('ACTIVE', 'Aktywne'),
                    ('BLOCKED', 'Zablokowane'),
                    ('DELETED', 'Usunięte'),
                ], default='ACTIVE', max_length=50)),
                ('emailVerified', models.BooleanField(default=False)),
                ('registrationDate', models.DateTimeField(auto_now_add=True)),
            ],
            options={'indexes': [models.Index(fields=['email'], name='email_idx')]},
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('user_ptr', models.OneToOneField(
                    auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                    parent_link=True, primary_key=True, serialize=False,
                    to='ExtLearnerUJ.user',
                )),
            ],
            bases=('ExtLearnerUJ.user',),
        ),
        migrations.CreateModel(
            name='Moderator',
            fields=[
                ('user_ptr', models.OneToOneField(
                    auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                    parent_link=True, primary_key=True, serialize=False,
                    to='ExtLearnerUJ.user',
                )),
            ],
            bases=('ExtLearnerUJ.user',),
        ),
        migrations.CreateModel(
            name='Admin',
            fields=[
                ('user_ptr', models.OneToOneField(
                    auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                    parent_link=True, primary_key=True, serialize=False,
                    to='ExtLearnerUJ.user',
                )),
            ],
            bases=('ExtLearnerUJ.user',),
        ),

        # ===== Sesje i tokeny =====
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('userId', models.CharField(db_index=True, max_length=255)),
                ('token', models.CharField(max_length=255, unique=True)),
                ('expiresAt', models.DateTimeField(
                    default=ExtLearnerUJ.models._default_session_expiry)),
            ],
        ),
        migrations.CreateModel(
            name='EmailVerificationToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('userId', models.CharField(db_index=True, max_length=255)),
                ('token', models.CharField(
                    default=ExtLearnerUJ.models._default_email_token,
                    max_length=10)),
                ('expiresAt', models.DateTimeField(
                    default=ExtLearnerUJ.models._default_email_token_expiry)),
            ],
        ),

        # ===== Materiały =====
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField(blank=True)),
                ('authorId', models.CharField(db_index=True, max_length=255)),
                ('category', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(choices=[
                    ('PENDING', 'Oczekuje'),
                    ('VERIFIED', 'Zweryfikowany'),
                    ('REJECTED', 'Odrzucony'),
                ], default='PENDING', max_length=50)),
                ('priority', models.IntegerField(default=0)),
                ('isVerified', models.BooleanField(default=False)),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-priority', '-id']},
        ),
        migrations.CreateModel(
            name='FileAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('fileName', models.CharField(max_length=255)),
                ('filePath', models.CharField(max_length=500)),
                ('fileType', models.CharField(blank=True, max_length=50)),
                ('sizeBytes', models.BigIntegerField(default=0)),
                ('uploadedAt', models.DateTimeField(auto_now_add=True)),
                ('material', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attachments', to='ExtLearnerUJ.material',
                )),
            ],
        ),

        # ===== Testy =====
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('type', models.CharField(default='MATERIAL', max_length=50)),
                ('materialId', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='DiagnosticTest',
            fields=[
                ('test_ptr', models.OneToOneField(
                    auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                    parent_link=True, primary_key=True, serialize=False,
                    to='ExtLearnerUJ.test',
                )),
            ],
            bases=('ExtLearnerUJ.test',),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('qType', models.CharField(default='SINGLE_CHOICE', max_length=50)),
                ('options', models.JSONField(blank=True, default=list)),
                ('correctAnswer', models.CharField(max_length=255)),
                ('points', models.IntegerField(default=1)),
                ('area', models.CharField(blank=True, max_length=50)),
                ('test', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='questions', to='ExtLearnerUJ.test',
                )),
            ],
        ),
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('testId', models.CharField(db_index=True, max_length=255)),
                ('userId', models.CharField(db_index=True, max_length=255)),
                ('score', models.FloatField(default=0.0)),
                ('answers', models.JSONField(default=dict)),
                ('completedAt', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='DiagnosticResult',
            fields=[
                ('testresult_ptr', models.OneToOneField(
                    auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                    parent_link=True, primary_key=True, serialize=False,
                    to='ExtLearnerUJ.testresult',
                )),
                ('areaScores', models.JSONField(default=dict)),
            ],
            bases=('ExtLearnerUJ.testresult',),
        ),

        # ===== Encje pod Sprint 2 (szkielety — bez logiki na razie) =====
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('userId', models.CharField(max_length=255)),
                ('materialId', models.CharField(max_length=255)),
                ('addedAt', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('userId', models.CharField(max_length=255)),
                ('materialId', models.CharField(max_length=255)),
                ('votedAt', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('userId', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('isRead', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Work',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('studentId', models.CharField(max_length=255)),
                ('packageId', models.CharField(max_length=255)),
                ('status', models.CharField(default='PENDING', max_length=50)),
                ('assignedModeratorId',
                 models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('price', models.FloatField(default=0.0)),
                ('scope', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('workId', models.CharField(max_length=255)),
                ('userId', models.CharField(max_length=255)),
                ('amount', models.FloatField(default=0.0)),
                ('status', models.CharField(default='PENDING', max_length=50)),
                ('method', models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='WorkReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('workId', models.CharField(max_length=255)),
                ('moderatorId', models.CharField(max_length=255)),
                ('grade', models.CharField(blank=True, max_length=50)),
                ('generalComment', models.TextField(blank=True)),
                ('status', models.CharField(default='DRAFT', max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='ErrorMark',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('reviewId', models.CharField(max_length=255)),
                ('textSnippet', models.TextField()),
                ('type', models.CharField(max_length=50)),
                ('positionInText',
                 models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='MaterialVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('materialId', models.CharField(max_length=255)),
                ('moderatorId', models.CharField(max_length=255)),
                ('decision', models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='ModeratorApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('candidateId', models.CharField(max_length=255)),
                ('status', models.CharField(default='PENDING', max_length=50)),
                ('testResultId', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('reporterId', models.CharField(max_length=255)),
                ('targetType', models.CharField(max_length=50)),
                ('targetId', models.CharField(max_length=255)),
                ('reason', models.TextField()),
                ('status', models.CharField(default='PENDING', max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Statistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
            ],
        ),
    ]
