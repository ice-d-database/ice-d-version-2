import os

from base.models import DataFileMigration
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.backends.utils import logger
from django.utils import timezone


class Command(BaseCommand):
    help = "Insert existing data into database"

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--folder",
            type=str,
            help="Folder where sql files exist to run for data insert",
        )
        parser.add_argument(
            "-m",
            "--mask",
            type=str,
            help="Mask used to prefix file name. Default: 0000",
        )

    def handle(self, *args, **kwargs):
        folder = kwargs["folder"]
        print(folder)
        if kwargs["mask"] is not None:
            mask = kwargs["mask"]
        else:
            mask = "0000"

        sqlFiles = []
        sqlToRun = []

        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".sql"):
                    sqlFiles.append(file)

        sqlFiles.sort()

        logger.info(str(len(sqlFiles)) + " SQL File(s) Found!")

        inserted = list(DataFileMigration.objects.all().values_list("name", flat=True))
        if inserted is not None:

            for name in sqlFiles:
                if name not in inserted:
                    sqlToRun.append(name)
        else:
            sqlToRun = sqlFiles

        sqlToRun.sort()

        logger.info(str(len(sqlToRun)) + " New SQL File(s) Found!")

        for sqlFile in sqlToRun:
            self.load_data_from_sql(folder, sqlFile)

    def load_data_from_sql(self, folder: str, filename: str):
        logger.info("Inserting " + str(filename) + " Data")
        file_path = os.path.join(os.path.dirname(__file__), folder, filename)
        sql_statement = open(file_path).read()
        with connection.cursor() as c:
            c.execute(sql_statement)

        DataFileMigration(name=filename, applied=timezone.now()).save()

        logger.info(str(filename) + " Data inserted!")
