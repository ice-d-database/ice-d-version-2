# Generated by Django 3.2.6 on 2021-10-31 17:05

from django.db import connection, migrations


def load_base_data(apps, schema_editor):
    Calculation = apps.get_model("base", "Calculation")
    Application = apps.get_model("base", "Application")
    Continent = apps.get_model("base", "Continent")

    Calculation(
        name="age_input_v3",
        calculation_service_endpoint="http://stoneage.ice-d.org/cgi-bin/matweb",
        variable_json='{"mlmfile": "age_input_v3", "reportType": "XML", "resultType": "long", "summary": "<summary>", "plotFlag": "yes", "text_block": "<calculation string>"}',
    ).save()

    Calculation(
        name="Cl36_input_v3",
        calculation_service_endpoint="http://stoneage.ice-d.org/cgi-bin/matweb",
        variable_json='{"mlmfile" : "Cl36_input_v3", "reportType" : "XML", "summary" : "<summary>", "plotFlag" : "yes", "text_block" : "<calculation string>"}',
    ).save()

    Calculation(
        name="al_be_age_many_v22_ws",
        calculation_service_endpoint="http://hess.ess.washington.edu/cgi-bin/matweb",
        variable_json='{"mlmfile" : "al_be_age_many_v22_ws", "P10_St" : "3.93089", "delP10_St" : "0.18857", "P10_Lm" : "3.87397", "delP10_Lm" : "0.18737", "P26_St" : "26.5335", "delP26_St" : "1.2728", "P26_Lm" : "26.1493", "delP26_Lm" : "1.2647", "text_block" : "<calculation string>"}',
    ).save()

    Application(
        image="antarctica_app.jpg",
        description="All known cosmogenic-nuclide data from Antarctica",
        name="Antarctica",
        map_image="http://stoneage.ice-d.org/iced/current_AA_map.png",
        NSF_funding=True,
    ).save()

    Application(
        image="alpine_app.png",
        description="Cosmogenic-nuclide exposure-age data from alpine glacial landforms worldwide",
        name="Alpine",
        interactive_map=True,
    ).save()

    Application(
        image="greenland_app.png",
        description="Cosmogenic-nuclide exposure-age data relevant to the Greenland Ice Sheet",
        name="Greenland",
        map_image="http://stoneage.ice-d.org/iced/current_GL_map.png",
        credits="Greg Balco, Allie Balter-Kennedy, Jason Briner, Brandon Graham, Jennifer Lamp, Alia Lesnek, Joe Tulenko, Caleb Walcott, Perry Spector",
    ).save()

    Application(
        image="tectonics_app.png",
        description="Cosmogenic-nuclide exposure-age data (NEED UPDATED DESCRIPTION)",
        name="Tectonics",
        interactive_map=True,
    ).save()

    Application(
        image="productionrate_app.jpg",
        description="Geological calibration data needed to estimate cosmogenic-nuclide production rates",
        name="Production Rate Calibration Data",
        map_image="http://stoneage.ice-d.org/iced/current_cal_map.png",
        calibration_data_sets=True,
        interactive_map=True
    ).save()

    # Note - continents aren't just the world continents. Certain areas might require other values, such as
    # Greenland, or Islands etc.
    Continent(
        name="North America"
    ).save()  # Note - slug is generated via django-autoslug

    Continent(
        name="South America"
    ).save()  # Note - slug is generated via django-autoslug

    Continent(name="Europe").save()  # Note - slug is generated via django-autoslug

    Continent(name="Asia").save()  # Note - slug is generated via django-autoslug

    Continent(name="Africa").save()  # Note - slug is generated via django-autoslug

    Continent(name="Oceania").save()  # Note - slug is generated via django-autoslug

    Continent(name="Antarctica").save()  # Note - slug is generated via django-autoslug

    Continent(name="Greenland").save()  # Note - slug is generated via django-autoslug

    Continent(name="Island(s)").save()  # Note - slug is generated via django-autoslug

    Continent(
        name="Not Applicable"
    ).save()  # Note - slug is generated via django-autoslug


class Migration(migrations.Migration):
    dependencies = [
        ("base", "0002_legacy_db_load"),
    ]

    operations = [migrations.RunPython(load_base_data)]
