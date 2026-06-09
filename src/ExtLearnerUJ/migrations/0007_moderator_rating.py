"""Oceny sprawdzających (1-5 gwiazdek) wystawiane przez zleceniodawców."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ExtLearnerUJ', '0006_application_test_and_notification_details'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModeratorRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('workId', models.CharField(db_index=True, max_length=255)),
                ('studentId', models.CharField(db_index=True, max_length=255)),
                ('moderatorId', models.CharField(db_index=True, max_length=255)),
                ('score', models.PositiveSmallIntegerField()),
                ('comment', models.TextField(blank=True)),
                ('createdAt', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'unique_together': {('workId', 'studentId')},
            },
        ),
    ]
