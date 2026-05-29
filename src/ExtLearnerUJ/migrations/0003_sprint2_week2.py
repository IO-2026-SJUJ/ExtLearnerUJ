"""Migracja tydzień 2 Sprintu 2 — Work, Package, PaymentTransaction,
WorkReview, ErrorMark + FK Work w FileAttachment."""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ExtLearnerUJ', '0002_sprint2'),
    ]

    operations = [
        # ---- Work: pełne statusy + submittedAt + indeksy ----
        migrations.AlterField(
            model_name='work',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING_PAYMENT', 'Oczekuje na płatność'),
                    ('PAID', 'Opłacone — w kolejce'),
                    ('IN_REVIEW', 'W trakcie sprawdzania'),
                    ('REVIEWED', 'Sprawdzone'),
                    ('CANCELLED', 'Anulowane'),
                ],
                default='PENDING_PAYMENT',
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='work',
            name='studentId',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AddField(
            model_name='work',
            name='submittedAt',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddIndex(
            model_name='work',
            index=models.Index(fields=['status', 'submittedAt'], name='work_stat_idx'),
        ),
        migrations.AlterModelOptions(
            name='work',
            options={'ordering': ['-submittedAt']},
        ),

        # ---- Package: description + ordering ----
        migrations.AddField(
            model_name='package',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterModelOptions(
            name='package',
            options={'ordering': ['price']},
        ),

        # ---- PaymentTransaction: createdAt + completedAt + index po workId ----
        migrations.AddField(
            model_name='paymenttransaction',
            name='createdAt',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='paymenttransaction',
            name='completedAt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='paymenttransaction',
            name='workId',
            field=models.CharField(db_index=True, max_length=255),
        ),

        # ---- WorkReview: createdAt + publishedAt + index ----
        migrations.AddField(
            model_name='workreview',
            name='createdAt',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='workreview',
            name='publishedAt',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='workreview',
            name='workId',
            field=models.CharField(db_index=True, max_length=255),
        ),

        # ---- ErrorMark: comment + choices dla type + ordering ----
        migrations.AddField(
            model_name='errormark',
            name='comment',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='errormark',
            name='createdAt',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='errormark',
            name='type',
            field=models.CharField(
                choices=[
                    ('GRAMMAR', 'Błąd gramatyczny'),
                    ('UNNATURAL', 'Nienaturalne sformułowanie'),
                    ('POSITIVE', 'Dobre sformułowanie'),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name='errormark',
            name='reviewId',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterModelOptions(
            name='errormark',
            options={'ordering': ['createdAt']},
        ),

        # ---- FileAttachment: FK do Work ----
        migrations.AddField(
            model_name='fileattachment',
            name='work',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='attachments', to='ExtLearnerUJ.work',
            ),
        ),
    ]
