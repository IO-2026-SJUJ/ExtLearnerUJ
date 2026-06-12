"""Poprawki: wynik testu kwalifikacyjnego we wniosku moderatorskim
oraz pole „szczegóły" (komentarz do wglądu) w powiadomieniach."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ExtLearnerUJ', '0005_sprint3_fixes'),
    ]

    operations = [
        migrations.AddField(
            model_name='moderatorapplication',
            name='testScore',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='details',
            field=models.TextField(blank=True, default=''),
        ),
    ]
