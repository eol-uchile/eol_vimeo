# Generated by Django 2.2.24 on 2021-09-10 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eol_vimeo', '0004_auto_20210730_1619'),
    ]

    operations = [
        migrations.AddField(
            model_name='eolvimeovideo',
            name='expiry_at',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='eolvimeovideo',
            name='token',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]
