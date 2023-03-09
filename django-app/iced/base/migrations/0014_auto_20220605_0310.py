# Generated by Django 3.2.6 on 2022-06-05 03:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0013_site_older_than'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagefilescores',
            name='image_url_path',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='base.imageurlpath'),
        ),
        migrations.AlterField(
            model_name='site',
            name='older_than',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
