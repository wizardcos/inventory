# Generated by Django 4.0.3 on 2024-06-27 06:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('imsApp', '0007_invoice_date_created_invoice_date_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='imsApp.category'),
        ),
    ]
