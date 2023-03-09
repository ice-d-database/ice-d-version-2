from subprocess import call

from django.core.management.base import BaseCommand

from ..utils import pipenv_run


class Command(BaseCommand):
    help = "Runs style (black, and isort) on all files within the application."

    def add_arguments(self, parser):
        parser.add_argument("--write", dest="write", action="store_true")

    def handle(self, *args, **options):
        write = options["write"]

        black_cmd = ["black", "--check", "."]
        isort_cmd = ["isort", ".", "--diff"]

        if write:
            black_cmd.pop(1)
            isort_cmd.pop(2)

        self.stdout.write(self.style.SUCCESS("\n\n~~Running black~~"))
        call(pipenv_run(black_cmd))
        self.stdout.write(self.style.SUCCESS("~~End of black~~"))
        self.stdout.write(self.style.SUCCESS("\n\n~~Running isort~~"))
        call(pipenv_run(isort_cmd))
        self.stdout.write(self.style.SUCCESS("~~End of isort~~"))
