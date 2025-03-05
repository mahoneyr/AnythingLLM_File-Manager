import os
import time
from datetime import datetime

import requests
from django.utils import timezone

from .models import FileInfo, TaskError, created_workspaces

# host_folder = "/app/KornIntelligenz"
host_folder = "C:/Users/Ron.Metzger/Documents/!!testing_files"
AnythingLLM_api = "0FT7FNZ-GGJMCV3-Q28DBE2-ZGZ07BP"
main_url = "http://192.168.80.35:3003"
get_workspaces_url = "/api/v1/workspaces"
get_documents_url = "/api/v1/documents"
delete_documents_url = "/api/v1/system/remove-documents"
post_document_add_url = "/api/v1/document/upload"
create_folder_url = "/api/v1/document/create-folder"
move_to_folder_url = "/api/v1/document/move-files"
get_workspace_url = "/api/v1/workspace/"
update_embeddings_url = "/update-embeddings"
new_workspace_url = "/api/v1/workspace/new"
files_to_add = []
files_that_changed = []

update_embeddings = []  # [foldername,filename]

headers_json = {
    "accept": "application/json",
    "Authorization": f"Bearer {AnythingLLM_api}",
    "Content-Type": "application/json",
}


# TODO new_folders_to_workspaces = []
def check_all_servers():
    try:
        print("Files in the SQL Database: ", len(FileInfo.objects.all()))

        print("checking for deleted files")
        files_got_deleted = check_for_files_still_exist()
        print(f"{len(files_got_deleted)} has been deleted")

        print("checking all files")
        check_subfolder(host_folder, host_folder, True)
        print(
            f"found {len(files_to_add)} files to add and {len(files_that_changed)} files that changed:"
        )

        print("adding files to anythingLLM")
        add_files_to_anythingLLM(files_to_add)
        print("we now have so many db entries: ", len(FileInfo.objects.all()))

        print("deleting files from anythingLLM")
        delete_files_from_anythingLLM(files_got_deleted)
        print("after deletion we only have: ", len(FileInfo.objects.all()))

        print("updating files that have changed: ")
        update_files_in_anythingLLM(files_that_changed)
        print("after updating changed files we have: ", len(FileInfo.objects.all()))

        print("updating embeddings with ", update_embeddings)
        update_workspace_embeddings(update_embeddings)

        time.sleep(3)
        print("deleting unused workspaces")
        delete_unused_workspaces()

        print("Task executed successfully")
        TaskError.objects.create(success=True, error=None)
        print(len(FileInfo.objects.all()))
    except Exception as e:
        print(f"Error in task execution: {e}")
        TaskError.objects.create(success=False, error=str(e))


def list_files(directory):
    try:
        files = os.listdir(directory)
        return files
    except Exception as e:
        print(f"Error when reading files: {e}")


def check_subfolder(directory, main_folder, first_run):

    files = list_files(directory)
    for file in files:

        file_path = os.path.join(directory, file)
        isdir = os.path.isdir(file_path)
        if isdir:

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
                found_created_at = timezone.make_aware(
                    datetime.fromtimestamp(creation_time)
                )
                found_modified_at = timezone.make_aware(
                    datetime.fromtimestamp(modification_time)
                )
                if (
                    file_in_db.file_size != found_file_size
                    or file_in_db.created_at < found_created_at
                    or file_in_db.modified_at < found_modified_at
                ):
                    # if file has clearly changed:
                    files_that_changed.append([file_path, main_folder, file_name])
                    print(f"File {file_name} has changed.")


def check_for_files_still_exist():
    files_got_deleted = []
    all_files = FileInfo.objects.all()
    for file in all_files:
        if not os.path.exists(file.absolute_path):
            # if file doesnt exist anymore
            files_got_deleted.append(
                [file.absolute_path, file.main_folder, file.filename]
            )
            file.delete()
    return files_got_deleted


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

            # print(f"Uploading {file_path} to folder '{folder_name}'")
            response = requests.post(
                main_url + post_document_add_url,
                headers=headers_files,
                files=files,
                timeout=30,  # Increased timeout for file uploads
            )
            # print(response.json())
            doc_info = response.json()["documents"]
            location = doc_info[0]["location"]
            # print(f"location is {location}")
            response = requests.post(
                main_url + create_folder_url,
                headers=headers_json,
                json={"name": folder_name},
                timeout=10,
            )
            start = location.find("/") + 1
            only_file_name = location[start:]
            change_folder_json = {
                "files": [{"from": location, "to": f"{folder_name}/{only_file_name}"}]
            }
            # print(only_file_name)
            response = requests.post(
                main_url + move_to_folder_url,
                headers=headers_json,
                json=change_folder_json,
                timeout=10,
            )

            if response.status_code == 200:
                # Save the file info to our database if upload was successful
                saveFile(file_path, folder_name)
                update_embeddings.append([folder_name, only_file_name])


def delete_files_from_anythingLLM(array_to_delete):
    # Convert array format for AnythingLLM comparison
    files_to_delete = [[file[2], file[1]] for file in array_to_delete]

    try:
        # Get all documents from AnythingLLM
        response = requests.get(
            main_url + get_documents_url, headers=headers_json, timeout=10
        )
        response.raise_for_status()
        local_files = response.json()["localFiles"]
        folders = local_files["items"]

        # Build list of files to delete from AnythingLLM
        paths_to_delete = []
        for folder in folders:
            folder_name = folder["name"]
            for doc in folder["items"]:
                if [doc["title"], folder_name] in files_to_delete:
                    doc_path = f"{folder_name}/{doc['name']}"
                    paths_to_delete.append(doc_path)

        # Delete from AnythingLLM if we found any files
        if paths_to_delete:
            response = requests.delete(
                main_url + delete_documents_url,
                headers=headers_json,
                json={"names": paths_to_delete},
                timeout=10,
            )
            response.raise_for_status()

        # Delete from database
        for file in array_to_delete:
            FileInfo.objects.filter(filename=file[2], absolute_path=file[0]).delete()

    except requests.exceptions.RequestException as e:
        raise Exception(f"Error communicating with AnythingLLM: {str(e)}")
    except Exception as e:
        raise Exception(f"Error in delete_files_from_anythingLLM: {str(e)}")


def update_files_in_anythingLLM(files_that_changed):
    # First, remove ALL existing entries for these files from DB
    for file in files_that_changed:
        filename = file[2]
        filepath = file[0]
        # Delete all entries with this filename and path
        FileInfo.objects.filter(filename=filename, absolute_path=filepath).delete()

    # Then delete from AnythingLLM
    delete_files_from_anythingLLM(files_that_changed)

    # Finally add the new versions
    add_files_to_anythingLLM(files_that_changed)


def update_workspace_embeddings(list_of_new_embeddings):
    checked_workspaces = []
    workspaces_to_update = {}
    for new_workspace in list_of_new_embeddings:
        workspace_name = new_workspace[0]  # name
        if workspace_name not in checked_workspaces:  # check or create workspace
            checked_workspaces.append(workspace_name)
            response = requests.get(
                url=main_url
                + get_workspace_url
                + str.lower(workspace_name).replace(" ", ""),
                headers=headers_json,
                timeout=10,
            )
            if len(response.json()["workspace"]) == 0:
                print("does not exist")
                new_workspace_json = {
                    "name": workspace_name,
                    "similarityThreshold": 0.25,
                    "openAiTemp": 0.7,
                    "openAiHistory": 20,
                    "openAiPrompt": "Given the following conversation, relevant context, and a follow up question, reply with an answer to the current question the user is asking. Return only your response to the question given the above information following the users instructions as needed.",
                    "queryRefusalResponse": "There is no relevant information in this workspace to answer your query.",
                    "chatMode": "chat",
                    "topN": 4,
                }
                print("adding workspace to DB")
                created_workspaces.objects.create(name=workspace_name)
                print(f"now have {len(created_workspaces.objects.all())} workspaces")
                response = requests.post(
                    url=main_url + new_workspace_url,
                    headers=headers_json,
                    json=new_workspace_json,
                    timeout=10,
                )
                print(response.json())

        file_name = new_workspace[1]
        if workspace_name in workspaces_to_update:
            workspaces_to_update[workspace_name].append(f"{workspace_name}/{file_name}")
        else:
            workspaces_to_update[workspace_name] = [f"{workspace_name}/{file_name}"]

    for key, val in workspaces_to_update.items():
        json_to_send = {"adds": val, "deletes": []}
        print(json_to_send)
        requests.post(
            url=main_url
            + get_workspace_url
            + key.replace(" ", "")
            + update_embeddings_url,
            headers=headers_json,
            json=json_to_send,
            timeout=10,
        )


def delete_unused_workspaces():
    all_created_workspaces = created_workspaces.objects.all()
    for workspace in all_created_workspaces:
        response = requests.get(
            url=main_url
            + get_workspace_url
            + str.lower(workspace.name).replace(" ", ""),
            headers=headers_json,
            timeout=10,
        )
        workspace_data = response.json()["workspace"]
        print("tis is workspace data:", workspace_data)
        if len(workspace_data) != 0:
            this_workspace = workspace_data[0]
            print(this_workspace["documents"])
            if len(this_workspace["documents"]) == 0:
                response = requests.delete(
                    url=main_url
                    + get_workspace_url
                    + str.lower(workspace.name).replace(" ", ""),
                    headers=headers_json,
                    timeout=10,
                )
                print("deleted ", workspace.name)
                workspace.delete()


def saveFile(file_path, main_folder):
    # First ensure any existing entries are removed
    FileInfo.objects.filter(
        filename=os.path.basename(file_path), absolute_path=os.path.abspath(file_path)
    ).delete()

    # Now create the new entry
    creation_time = os.path.getctime(file_path)
    modification_time = os.path.getmtime(file_path)
    found_created_at = timezone.make_aware(datetime.fromtimestamp(creation_time))
    found_modified_at = timezone.make_aware(datetime.fromtimestamp(modification_time))

    return FileInfo.objects.create(
        filename=os.path.basename(file_path),
        absolute_path=os.path.abspath(file_path),
        main_folder=main_folder,
        file_size=os.path.getsize(file_path),
        created_at=found_created_at,
        modified_at=found_modified_at,
    )
