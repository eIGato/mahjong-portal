# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2017-12-28 14:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0002_player_ema_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='ema_id',
            field=models.CharField(blank=True, default='', max_length=30, null=True),
        ),
    ]