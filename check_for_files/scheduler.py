from django_q.models import Schedule


def setup_schedules():
    # Lösche eventuell vorhandene Schedules mit dem gleichen Namen
    Schedule.objects.filter(name="check_files_schedule").delete()

    # Erstelle einen neuen Schedule
    Schedule.objects.create(
        name="check_files_schedule",
        func="check_for_files.tasks.check_all_servers",  # Angepasst an die neue App
        schedule_type=Schedule.CRON,
        # Führe alle 15 Minuten aus
        cron="*/60 * * * *",  # Alle 15 Minuten, 24/7
        repeats=-1,  # Unendlich wiederholen
    )
