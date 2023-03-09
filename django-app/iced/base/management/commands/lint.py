from subprocess import call

from django.core.management.base import BaseCommand

from ..utils import pipenv_run


class Command(BaseCommand):
    help = "Runs lints (flake8, and mypy) on all files within the application."

    def handle(self, *args, **options):
        mypy_cmd = ["mypy", "./iced"]
        flake8_cmd = ["flake8"]

        self.stdout.write(self.style.SUCCESS("\n\n~~Running mypy~~"))
        call(pipenv_run(mypy_cmd))
        self.stdout.write(self.style.SUCCESS("~~End of mypy~~"))
        self.stdout.write(self.style.SUCCESS("\n\n~~Running flake8~~"))
        call(pipenv_run(flake8_cmd))
        self.stdout.write(self.style.SUCCESS("~~End of flake8~~"))
