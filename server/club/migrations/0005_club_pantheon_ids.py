# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-01-30 11:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0004_auto_20180127_0531'),
    ]

    operations = [
        migrations.AddField(
            model_name='club',
            name='pantheon_ids',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]