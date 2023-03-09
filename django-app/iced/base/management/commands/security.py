from subprocess import call

from django.core.management.base import BaseCommand

from ..utils import pipenv_run


class Command(BaseCommand):
    help = "Runs lints (flake8, and mypy) on all files within the application."

    def handle(self, *args, **options):
        bandit_cmd = ["bandit", "-c", "bandit_conf.yaml", "-r", "."]

        self.stdout.write(self.style.SUCCESS("\n\n~~Running bandit~~"))
        call(pipenv_run(bandit_cmd))
        self.stdout.write(self.style.SUCCESS("~~End of bandit~~"))
