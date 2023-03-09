import logging
import os
import requests
import json

from pathlib import Path
from typing import Optional
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import connection, transaction
from django.db.models import Q
from django.conf import settings

from .calculate_ages_utils import parse_and_insert
from base.models import Calculation, Job, Sample, CalculatedAge, Cl36
from base.queries import cl36_calculator_string_query


logname = Path.joinpath(settings.LOG_DIR, "calculate_ages_cl36")
file_handler = logging.handlers.TimedRotatingFileHandler(logname, when="W0", interval=1, backupCount=14)
file_handler.suffix = "%Y%m%d"
stream_handler = logging.StreamHandler()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[file_handler, stream_handler]
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs the ages calculations"
    name = "Calculate Ages CL36"
    calculation_name = "Cl36_input_v3"
    run_calculation_endpoint = (
        str(os.environ.get("BASE_URL")) + "/api/calculations/run/" + calculation_name
    )
    get_calculation_endpoint = (
        str(os.environ.get("BASE_URL")) + "/api/calculations/name/" + calculation_name
    )

    def get_sample_ids(self, last_run: Optional[datetime]=None, last_id: Optional[int]=None):
        queryset = Cl36.objects.select_related('sample')
        if last_run and last_id:
            queryset = queryset.filter(Q(sample__updated_at__gt=last_run) | Q(sample__id__gt=last_id))

        return list(queryset.distinct().values_list("sample__id", flat=True).order_by('sample__id')), timezone.now()

    def handle(self, *args, **kwargs):
        logger.info(f"- Job [{self.name}] start -")
        try:
            job = Job.objects.get(name=self.name)
        except Job.DoesNotExist:
            job = Job(name=self.name)
            job.save()

        highest_id = job.last_id if job.last_id else None
        sample_ids, timestamp = self.get_sample_ids(job.last_run, highest_id)

        if len(sample_ids) > 0:
            temp_high = sample_ids[-1]
            if highest_id is None:
                highest_id = temp_high
            else:
                highest_id = highest_id if highest_id > temp_high else temp_high

            cursor = connection.cursor()
            sql = cl36_calculator_string_query(sample_ids)
            cursor.execute(sql)

            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            calculation = Calculation.get_calculation_by_name(self.calculation_name)
            params = json.loads(calculation.variable_json)
            params[
                "summary"
            ] = "yes"  # Quoted from legacy_dbs code --> This is a bug in the m-file -- it will only accept 'yes'.

            with transaction.atomic():
                try:
                    CalculatedAge.objects.filter(sample_id__in=[row['id'] for row in rows]).delete()
                except Exception as e:
                    logger.warn(f"Error occured removing unique ids - {e}")
                    pass
                for row in rows:
                    calc_string = row['output']
                    if calc_string:
                        try:
                            logger.info(f"Getting calculation for {row['name']}")
                            params["text_block"] = calc_string
                            req = requests.request("GET", self.run_calculation_endpoint, data=json.dumps(params))
                            print(req.text)
                            logger.info(f"Parsing and inserting records for {row['name']}")
                            count = parse_and_insert(req.text, row['id'])
                            logger.info(f"Successfully created {count} records for {row['name']}")
                        except Exception as e:
                            logger.warn(f"Error occurred for record {row['name']} - {e}")
                            pass
                job.last_run = timestamp
                job.last_id = highest_id
            job.save()
        else:
            logger.info("No samples needing updates found.")
        logger.info(f"- Job [{self.name}] end -\n\n")


