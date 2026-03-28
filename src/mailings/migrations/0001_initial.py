from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OutgoingEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.CharField(max_length=128, unique=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='outgoing_emails', to=settings.AUTH_USER_MODEL)),
                ('email', models.EmailField()),
                ('subject', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('status', models.CharField(choices=[('PENDING', 'PENDING'), ('SENT', 'SENT'), ('ERROR', 'ERROR')], default='PENDING', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('last_error', models.TextField(blank=True, default='')),
            ],
        ),
    ]
