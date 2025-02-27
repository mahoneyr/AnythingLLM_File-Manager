import os

from .models import TaskError

host_folder = "/app/KornIntelligenz"


def check_all_servers():
    """
    Placeholder function that will be called by the scheduler.
    You can implement your specific logic here.
    """
    try:

        # Auflisten der Dateien im gemounteten Ordner
        list_files(host_folder)

        # Beispiel: Schreibe in eine Datei und lese sie anschließend aus
        write_file("test.txt", "Hallo, Docker Volume!")
        read_file("test.txt")

        print("Task executed successfully")
        TaskError.objects.create(success=True, error=None)
    except Exception as e:
        print(f"Error in task execution: {e}")
        TaskError.objects.create(success=False, error=str(e))


def list_files(directory):
    try:
        files = os.listdir(directory)
        print("Dateien im Verzeichnis:")
        for file in files:
            print(file)
    except Exception as e:
        print(f"Fehler beim Zugriff auf das Verzeichnis: {e}")


def read_file(filename):
    file_path = os.path.join(host_folder, filename)
    try:
        with open(file_path) as f:
            content = f.read()
            print(f"Inhalt der Datei {filename}:")
            print(content)
    except Exception as e:
        print(f"Fehler beim Lesen der Datei {filename}: {e}")


def write_file(filename, content):
    file_path = os.path.join(host_folder, filename)
    try:
        with open(file_path, "w") as f:
            f.write(content)
            print(f"Die Datei {filename} wurde erfolgreich geschrieben.")
    except Exception as e:
        print(f"Fehler beim Schreiben der Datei {filename}: {e}")
