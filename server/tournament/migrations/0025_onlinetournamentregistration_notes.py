# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-12-06 13:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0024_tournamentresult_country'),
    ]

    operations = [
        migrations.AddField(
            model_name='onlinetournamentregistration',
            name='notes',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Team name'),
        ),
    ]