from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0014_auto_20220605_0310'),
    ]

    operations = [
        migrations.RunSQL(  # NB: the usual (long, lat) is backwards here because MySQL 8 flipped them
            f"""ALTER TABLE {table} ADD COLUMN coord POINT GENERATED ALWAYS AS (ST_POINTFROMTEXT(
                CONCAT('POINT(', lat_DD, ' ', lon_DD, ')'),
                4326
            )) STORED COMMENT 'EPSG:4326 coordinates';""",
            reverse_sql="ALTER TABLE {table} DROP COLUMN coord;",
            state_operations=None,  # Django doesn't handle readonly generated columns as fields so no state here
        ) for table in ['base_core', 'base_sample']
    ]
