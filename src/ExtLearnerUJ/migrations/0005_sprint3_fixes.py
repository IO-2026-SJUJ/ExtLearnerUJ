"""Sprint 3 (poprawki) — termin blokady konta + tokeny resetu hasła."""
from django.db import migrations, models
import ExtLearnerUJ.models


class Migration(migrations.Migration):

    dependencies = [
        ('ExtLearnerUJ', '0004_sprint3'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='blockedUntil',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('userId', models.CharField(db_index=True, max_length=255)),
                ('token', models.CharField(
                    default=ExtLearnerUJ.models._default_reset_token,
                    max_length=64, unique=True)),
                ('expiresAt', models.DateTimeField(
                    default=ExtLearnerUJ.models._default_reset_expiry)),
                ('used', models.BooleanField(default=False)),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
