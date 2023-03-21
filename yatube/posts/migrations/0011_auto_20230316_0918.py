# Generated by Django 2.2.16 on 2023-03-16 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_comment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ('-created',), 'verbose_name': 'Комментарий', 'verbose_name_plural': 'Комментарии'},
        ),
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=models.TextField(max_length=200),
        ),
    ]
