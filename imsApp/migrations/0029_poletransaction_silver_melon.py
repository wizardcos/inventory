# Generated by Django 4.0.3 on 2024-07-21 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imsApp', '0028_poletransaction_arm_bend_poletransaction_arm_design_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='poletransaction',
            name='silver_melon',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
