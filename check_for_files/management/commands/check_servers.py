from django.core.management.base import BaseCommand

from check_for_files.tasks import check_all_servers


class Command(BaseCommand):
    help = "Runs the check_all_servers function from tasks.py"

    def handle(self, *args, **options):
        self.stdout.write("Starting server check...")
        try:
            check_all_servers()
            self.stdout.write(self.style.SUCCESS("Successfully completed server check"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during server check: {str(e)}"))
