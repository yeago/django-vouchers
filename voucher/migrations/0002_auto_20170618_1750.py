# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2017-06-18 17:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voucher', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voucher',
            name='voucher',
            field=models.CharField(max_length=50),
        ),
    ]