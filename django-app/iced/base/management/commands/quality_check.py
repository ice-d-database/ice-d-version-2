from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Runs lint, style, and security checks."

    def add_arguments(self, parser):
        parser.add_argument("--write", dest="write", action="store_true")

    def handle(self, *args, **options):
        write = options["write"]

        if write:
            call_command("style", "write")
        else:
            call_command("style")

        call_command("lint")
        call_command("security")
