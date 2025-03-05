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
delete_documents_url = "/api/v1/remove-documents"
post_document_add_url = "/api/v1/document/upload"
create_folder = "/api/v1/document/create-folder"
move_to_folder = "/api/v1/document/move-files"
files_to_add = []  # [file_path, main_folder_name]
files_that_changed = []  # [file_path, main_folder_name, file_name]
files_got_deleted = []  # [file_name, main_folder_name]

headers_json = {
    "accept": "application/json",
    "Authorization": f"Bearer {AnythingLLM_api}",
    "Content-Type": "application/json",
}


# TODO new_folders_to_workspaces = []
def check_all_servers():
    try:
        # files_got_deleted = check_for_files_still_exist() #return the files_got_deleted list
        check_subfolder(host_folder, host_folder, True)  # searches for files
        print("files_to_add: ", files_to_add)
        print("files_that_changed: ", files_that_changed)
        print("files_that_got_deleted: ", files_got_deleted)

        # lists are full, so now i can process everything

        # add_files_to_anythingLLM(files_to_add)
        delete_files_from_anythingLLM(files_to_add)  # TODO prob works

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
                files_to_add.append([file_path, main_folder, file_name])
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
                    files_that_changed.append([file_path, main_folder, file_name])
                    print(f"File {file_name} has changed.")


def check_for_files_still_exist():
    all_files = FileInfo.objects.all()
    for file in all_files:
        if not os.path.exists(file.absolute_path):
            print(f"File {file.filename} does not exist anymore.")
            files_got_deleted.append(
                [file.absolute_path, file.main_folder, file.filename]
            )
            file.delete()


def delete_files_from_anythingLLM(array_to_delete):

    # ------------------------
    # debugging:
    new_array = []
    for object in array_to_delete:
        new_array.append([object[2], object[1]])
    # --------------------------
    print("---------------------")
    print("start deleting")
    response = requests.get(
        main_url + get_documents_url, headers=headers_json, timeout=10
    )
    print("files found: ", response.json())
    local_files = response.json()["localFiles"]
    folders = local_files["items"]
    list_for_anythingLLM_request_deletion = []
    for folder in folders:
        all_docs = folder["items"]
        folder_name = folder["name"]
        for doc in all_docs:
            doc_title = doc["title"]
            doc_name = doc["name"]
            # print( "this is used for my check: " , [doc_title, folder_name])
            if [doc_title, folder_name] in new_array:

                doc_path_in_llm = f"{folder_name}/{doc_name}"
                # print(doc_path_in_llm, " is the pat")
                list_for_anythingLLM_request_deletion.append(doc_path_in_llm)
                # print(f"deleted {doc_title}, {doc_name} from anythingLLM ")

    print("list to delete is:", list_for_anythingLLM_request_deletion)
    delete_json = {"names": list_for_anythingLLM_request_deletion}
    print(delete_json)
    requests.delete(
        main_url + delete_documents_url,
        headers=headers_json,
        json=delete_json,
        timeout=10,
    )
    print("done")


def add_files_to_anythingLLM(files_to_add):
    headers_files = {
        "accept": "application/json",
        "Authorization": f"Bearer {AnythingLLM_api}",
    }
    for file in files_to_add:
        file_path = file[0]
        folder_name = file[1]

        # Open and prepare the file for upload
        with open(file_path, "rb") as f:
            files = {
                "file": (os.path.basename(file_path), f, "application/octet-stream")
            }

            print(f"Uploading {file_path} to folder '{folder_name}'")
            response = requests.post(
                main_url + post_document_add_url,
                headers=headers_files,
                files=files,
                timeout=30,  # Increased timeout for file uploads
            )
            print(response.json())
            doc_info = response.json()["documents"]
            location = doc_info[0]["location"]
            # print(f"location is {location}")
            response = requests.post(
                main_url + create_folder,
                headers=headers_json,
                json={"name": folder_name},
                timeout=10,
            )
            start = location.find("/") + 1
            only_file_name = location[start:]
            change_folder_json = {
                "files": [{"from": location, "to": f"{folder_name}/{only_file_name}"}]
            }
            print(only_file_name)
            response = requests.post(
                main_url + move_to_folder,
                headers=headers_json,
                json=change_folder_json,
                timeout=10,
            )

            # if response.status_code == 200:
            # Save the file info to our database if upload was successful
            # saveFile(file_path)


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
