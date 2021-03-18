# Generated by Django 3.1.7 on 2021-03-17 22:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentController', '0008_auto_20210317_2215'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='documentedits',
            constraint=models.UniqueConstraint(fields=('userId', 'documentId'), name='unique edits'),
        ),
    ]
