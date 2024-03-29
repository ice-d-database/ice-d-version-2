# Generated by Django 3.2.6 on 2022-11-17 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0015_add_generated_coordinate_columns'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='imagefile',
            name='urlpath',
        ),
        migrations.RemoveField(
            model_name='imagefilescores',
            name='urlpath',
        ),
        migrations.AlterField(
            model_name='core',
            name='name',
            field=models.CharField(db_index=True, max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='imagefile',
            name='image_type',
            field=models.CharField(choices=[('Field Image', 'Field Image'), ('Lab Image', 'Lab Image')], max_length=255),
        ),
        migrations.AlterField(
            model_name='sample',
            name='what',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='site',
            name='short_name',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='site',
            name='what',
            field=models.TextField(default=''),
        ),
    ]
