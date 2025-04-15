from django.core.management.base import BaseCommand

from check_for_files.tasks import main


class Command(BaseCommand):
    help = "Runs the main function from tasks.py"

    def handle(self, *args, **options):
        self.stdout.write("Starting server check...")
        try:
            main()
            self.stdout.write(self.style.SUCCESS("Successfully completed server check"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during server check: {str(e)}"))
