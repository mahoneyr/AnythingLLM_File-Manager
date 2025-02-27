from django_q.models import Schedule


def setup_schedules():
    # Lösche eventuell vorhandene Schedules mit dem gleichen Namen
    Schedule.objects.filter(name="check_servers_workdays").delete()

    # Erstelle einen neuen Schedule
    Schedule.objects.create(
        name="check_servers_workdays",
        func="pingLinks.tasks.check_all_servers",
        schedule_type=Schedule.CRON,
        # Führe alle 5 Minuten zwischen 9-17 Uhr an Arbeitstagen aus
        cron="*/10 8-17 * * 1-5",  # Minute 0-59/5, Stunden 9-17, alle Tage, alle Monate, Wochentage 1-5 (Mo-Fr)
        repeats=-1,  # Unendlich wiederholen
    )
