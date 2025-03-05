import os
import time
from datetime import datetime

import requests

from .models import FileInfo, TaskError

# host_folder = "/app/KornIntelligenz"
host_folder = "C:/Users/Ron.Metzger/Documents/!!testing_files"
AnythingLLM_api = "0FT7FNZ-GGJMCV3-Q28DBE2-ZGZ07BP"
main_url = "http://192.168.80.35:3003"
get_workspaces_url = "/api/v1/workspaces"
get_documents_url = "/api/v1/documents"
delete_documents_utl = "/api/v1/remove-documents"
post_document_add_url = "/api/v1/document/upload"
create_folder = "/api/v1/document/create-folder"
move_to_folder = "/api/v1/document/move-files"
files_to_add = []  # [file_path, main_folder_name]
files_that_changed = []  # [file_path, main_folder_name]
files_got_deleted = []


# TODO new_folders_to_workspaces = []
def check_all_servers():
    try:
        # files_got_deleted = check_for_files_still_exist() #return the files_got_deleted list
        check_subfolder(host_folder, host_folder, True)  # searches for files
        print("files_to_add: ", files_to_add)
        print("files_that_changed: ", files_that_changed)
        print("files_that_got_deleted: ", files_got_deleted)

        # lists are full, so now i can process everything
        # delete_files_from_anythingLLM(files_got_deleted)

        add_files_to_anythingLLM(files_to_add)

        # TODO update_files_in_anythingLLM(files_that_changed)

        print("Task executed successfully")
        TaskError.objects.create(success=True, error=None)
    except Exception as e:
        print(f"Error in task execution: {e}")
        TaskError.objects.create(success=False, error=str(e))


def check_subfolder(directory, main_folder, first_run):
    print(f"new subfolder check: {directory}, {main_folder}, {first_run}")
    files = list_files(directory)
    for file in files:
        print("checking ", file)
        file_path = os.path.join(directory, file)
        isdir = os.path.isdir(file_path)
        if isdir:
            print(f"{file_path} is a folder")
            check_subfolder(file_path, file, False)
            pass
        elif first_run:
            # we are ignoring the files in the base folder
            break
        else:
            file_name = os.path.basename(file_path)
            absolute_path = os.path.abspath(file_path)
            file_in_db = FileInfo.objects.filter(
                filename=file_name, absolute_path=absolute_path
            ).first()

            if file_in_db is None:
                files_to_add.append([file_path, main_folder])
                continue
            else:  # file already exists in db
                # check if file has changed:
                creation_time = os.path.getctime(file_path)
                modification_time = os.path.getmtime(file_path)

                found_file_size = os.path.getsize(file_path)
                found_created_at = datetime.fromtimestamp(creation_time)
                found_modified_at = datetime.fromtimestamp(modification_time)
                if (
                    file_in_db.file_size != found_file_size
                    or file_in_db.created_at < found_created_at
                    or file_in_db.modified_at < found_modified_at
                ):
                    # if file has clearly changed:
                    files_that_changed.append([file_path, main_folder])
                    print(f"File {file_name} has changed.")


def check_for_files_still_exist():
    all_files = FileInfo.objects.all()
    for file in all_files:
        if not os.path.exists(file.absolute_path):
            print(f"File {file.filename} does not exist anymore.")
            files_got_deleted.append([file.filename, file.main_folder])
            file.delete()


def delete_files_from_anythingLLM(array_to_delete):
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {AnythingLLM_api}",
        "Content-Type": "application/json",
    }
    response = requests.get(main_url + get_documents_url, headers=headers, timeout=10)
    local_files = response.json()["localFiles"]
    folders = local_files["items"]

    list_for_anythingLLM_request_deletion = []
    for folder in folders:
        all_docs = folder["items"]
        folder_name = folder["name"]
        for doc in all_docs:
            doc_title = doc["title"]
            doc_name = doc["name"]
            if [doc_name, folder_name] in array_to_delete:
                doc_path_in_llm = f"{folder_name}/{doc_title}"
                list_for_anythingLLM_request_deletion.append(doc_path_in_llm)
                print(f"deleted {doc_title}, {doc_name} from anythingLLM ")

    delete_response = requests.delete(
        main_url + delete_documents_utl,
        headers=headers,
        json={"names": list_for_anythingLLM_request_deletion},
        timeout=10,
    )
    print(delete_response.json())


def add_files_to_anythingLLM(files_to_add):
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {AnythingLLM_api}",
        "Content-Type": "application/json",
    }
    for file in files_to_add:
        print(file[0])
        response = requests.post(
            main_url + post_document_add_url, headers=headers, json=file[0], timeout=10
        )
        print(response.json())


def list_files(directory):
    try:
        files = os.listdir(directory)
        print("Dateien im Verzeichnis:")
        for file in files:
            print(file)
        return files
    except Exception as e:
        print(f"Fehler beim Zugriff auf das Verzeichnis: {e}")


def saveFile(file_path):  # TODO (data) -> and actually save it, add main_folder
    FileInfo.objects.create(
        filename=os.path.basename(file_path),
        absolute_path=os.path.abspath(file_path),
        file_size=os.path.getsize(file_path),
        # created_at=created_at,
        # modified_at=modified_at,
    )
