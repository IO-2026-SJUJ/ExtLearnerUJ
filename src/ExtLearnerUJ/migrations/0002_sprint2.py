"""Migracja Sprint 2 — rozszerzenie Vote, Notification, MaterialVerification,
Report i dodanie Comment."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ExtLearnerUJ', '0001_initial'),
    ]

    operations = [
        # ---- Vote: unique_together + index po materialId ----
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together={('userId', 'materialId')},
        ),
        migrations.AddIndex(
            model_name='vote',
            index=models.Index(fields=['materialId'], name='vote_mat_idx'),
        ),

        # ---- Notification: link + createdAt + ordering + indeks ----
        migrations.AddField(
            model_name='notification',
            name='link',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='notification',
            name='createdAt',
            field=models.DateTimeField(auto_now_add=True, null=True),
            # null=True tymczasowo, żeby ominąć problem z istniejącymi wierszami.
            # W produkcji: po migracji wypełnić i usunąć null=True.
        ),
        migrations.AlterField(
            model_name='notification',
            name='userId',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterModelOptions(
            name='notification',
            options={'ordering': ['-createdAt']},
        ),

        # ---- MaterialVerification: comment + verifiedAt + choices ----
        migrations.AddField(
            model_name='materialverification',
            name='comment',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='materialverification',
            name='verifiedAt',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='materialverification',
            name='decision',
            field=models.CharField(
                blank=True,
                choices=[
                    ('ACCEPTED', 'Zaakceptowany'),
                    ('REJECTED', 'Odrzucony'),
                    ('NEEDS_REVISION', 'Do poprawy'),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='materialverification',
            name='materialId',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterModelOptions(
            name='materialverification',
            options={'ordering': ['-verifiedAt']},
        ),

        # ---- Report: rozszerzenie ----
        migrations.AddField(
            model_name='report',
            name='createdAt',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='report',
            name='resolvedAt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='report',
            name='resolvedBy',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='report',
            name='reporterId',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='report',
            name='targetType',
            field=models.CharField(
                choices=[
                    ('MATERIAL', 'Materiał'),
                    ('USER', 'Użytkownik'),
                    ('COMMENT', 'Komentarz'),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='report',
            name='targetId',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='report',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Oczekuje'),
                    ('RESOLVED', 'Rozpatrzone'),
                    ('DISMISSED', 'Odrzucone'),
                ],
                default='PENDING',
                max_length=50,
            ),
        ),
        migrations.AddIndex(
            model_name='report',
            index=models.Index(fields=['status', 'createdAt'], name='report_stat_idx'),
        ),
        migrations.AlterModelOptions(
            name='report',
            options={'ordering': ['-createdAt']},
        ),

        # ---- Comment (nowy model) ----
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('authorId', models.CharField(max_length=255)),
                ('targetType', models.CharField(max_length=50)),
                ('targetId', models.CharField(db_index=True, max_length=255)),
                ('text', models.TextField()),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-createdAt']},
        ),
    ]
