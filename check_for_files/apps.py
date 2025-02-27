from django.apps import AppConfig


class PinglinksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "check_for_files"

    def ready(self):
        try:
            from .scheduler import setup_schedules

            setup_schedules()
        except Exception as e:
            print(f"Error setting up schedules: {e}")
            # Fehler hier nicht weitergeben, da dies den App-Start nicht blockieren soll
