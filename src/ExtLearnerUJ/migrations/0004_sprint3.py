"""Migracja Sprintu 3 — symulacja egzaminu z timerem (FR-06), gamifikacja /
ranking (FR-07), wnioski o rolę moderatora (FR-12) i wypłaty moderatorów
(FR-14).

Tylko dodaje pola i nowe modele — istniejące dane (diagnostyka, materiały,
prace) zostają nietknięte.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ExtLearnerUJ', '0003_sprint2_week2'),
    ]

    operations = [
        # ---- Test: limit czasu (FR-06) ----
        migrations.AddField(
            model_name='test',
            name='durationMinutes',
            field=models.IntegerField(default=0),
        ),

        # ---- ModeratorApplication: rozbudowa pod FR-12 ----
        migrations.AddField(
            model_name='moderatorapplication',
            name='motivation',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='moderatorapplication',
            name='certificatePath',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='moderatorapplication',
            name='decisionComment',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='moderatorapplication',
            name='createdAt',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='moderatorapplication',
            name='reviewedAt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='moderatorapplication',
            name='reviewedBy',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='moderatorapplication',
            name='candidateId',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='moderatorapplication',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Oczekuje'),
                    ('ACCEPTED', 'Zaakceptowany'),
                    ('REJECTED', 'Odrzucony'),
                ],
                default='PENDING',
                max_length=50,
            ),
        ),
        migrations.AlterModelOptions(
            name='moderatorapplication',
            options={'ordering': ['createdAt']},
        ),

        # ---- ExamAttempt: podejście do symulacji egzaminu (FR-06) ----
        migrations.CreateModel(
            name='ExamAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('testId', models.CharField(db_index=True, max_length=255)),
                ('userId', models.CharField(db_index=True, max_length=255)),
                ('status', models.CharField(
                    choices=[('IN_PROGRESS', 'W trakcie'), ('SUBMITTED', 'Zakończone')],
                    default='IN_PROGRESS', max_length=50)),
                ('answers', models.JSONField(default=dict)),
                ('score', models.FloatField(default=0.0)),
                ('areaScores', models.JSONField(default=dict)),
                ('pointsAwarded', models.IntegerField(default=0)),
                ('startedAt', models.DateTimeField(auto_now_add=True)),
                ('deadline', models.DateTimeField(blank=True, null=True)),
                ('submittedAt', models.DateTimeField(blank=True, null=True)),
            ],
            options={'ordering': ['-startedAt']},
        ),
        migrations.AddIndex(
            model_name='examattempt',
            index=models.Index(fields=['userId', 'status'], name='exam_user_status_idx'),
        ),

        # ---- UserStats: punkty rankingowe + agregaty (FR-07) ----
        migrations.CreateModel(
            name='UserStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('userId', models.CharField(db_index=True, max_length=255, unique=True)),
                ('points', models.IntegerField(default=0)),
                ('examsCompleted', models.IntegerField(default=0)),
                ('diagnosticsCompleted', models.IntegerField(default=0)),
                ('bestExamScore', models.FloatField(default=0.0)),
                ('updatedAt', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-points']},
        ),

        # ---- Payout: wypłaty moderatorów (FR-14) ----
        migrations.CreateModel(
            name='Payout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('moderatorId', models.CharField(db_index=True, max_length=255)),
                ('amount', models.FloatField(default=0.0)),
                ('status', models.CharField(
                    choices=[('PENDING', 'Oczekuje na realizację'), ('PAID', 'Zrealizowana')],
                    default='PENDING', max_length=50)),
                ('invoiceNumber', models.CharField(blank=True, max_length=64)),
                ('requestedAt', models.DateTimeField(auto_now_add=True)),
                ('paidAt', models.DateTimeField(blank=True, null=True)),
            ],
            options={'ordering': ['-requestedAt']},
        ),
    ]
