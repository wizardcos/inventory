# Generated by Django 4.0.3 on 2024-07-21 06:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imsApp', '0026_alter_poletransaction_order_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='customer_code',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='quantity',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='invoice_item',
            name='quantity',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='poletransaction',
            name='customer_code',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='poletransaction',
            name='quantity',
            field=models.CharField(max_length=100),
        ),
    ]
