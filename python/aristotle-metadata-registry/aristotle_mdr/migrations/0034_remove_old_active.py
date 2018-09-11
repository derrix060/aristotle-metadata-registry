# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('aristotle_mdr', '0033_ra_levels'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registrationauthority',
            name='active'
        ),
        migrations.RenameField(
            model_name='registrationauthority',
            old_name='new_active',
            new_name='active'
        )
    ]
