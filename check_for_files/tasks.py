import os
import time
from datetime import datetime

import requests
from django.utils import timezone

from .models import FileInfo, TaskError, created_workspaces

host_folder = "/app/AnythingLLM"

# Get AnythingLLM API key and URL from environment variables
AnythingLLM_api = os.environ.get("ANYTHING_LLM_API")
if not AnythingLLM_api:
    raise ValueError("ANYTHING_LLM_API environment variable is not set")

main_url = os.environ.get("ANYTHING_LLM_URL")
if not main_url:
    raise ValueError("ANYTHING_LLM_URL environment variable is not set")


# different urls parts for the API
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

# header for all the get, post and delete requests which needs jsons.
headers_json = {
    "accept": "application/json",
    "Authorization": f"Bearer {AnythingLLM_api}",
    "Content-Type": "application/json",
}


def anythingLLM_update():
    try:
        files_got_deleted = check_for_files_still_exist()

        check_subfolder(host_folder, host_folder, True)

        if (
            len(files_got_deleted) == 0
            and len(files_to_add) == 0
            and len(files_that_changed) == 0
        ):
            print("Since no changes have been detected, nothing happens")
            TaskError.objects.create(success=True, error="Early stop cause no changes")
            return

        print(
            f"Found {len(files_to_add)} files to add, {len(files_that_changed)} files that changed and {len(files_got_deleted)} files that got deleted. Updating AnythingLLM now"
        )

        add_files_to_anythingLLM(files_to_add)

        delete_files_from_anythingLLM(files_got_deleted)

        update_files_in_anythingLLM(files_that_changed)

        # waiting for uploads
        wait_time = len(files_to_add) + len(files_that_changed)
        time.sleep(wait_time * 3)
        update_workspace_embeddings(update_embeddings)
        delete_unused_workspaces()

        print(
            f"Done Updating, task was successful. {len(FileInfo.objects.all())} documents in DB"
        )
        TaskError.objects.create(success=True, error=None)

    except Exception as e:
        print(f"Error in task execution: {e}")
        TaskError.objects.create(success=False, error=str(e))


def list_files(directory):
    # returning a list of all files within a path
    try:
        files = os.listdir(directory)
        return files
    except Exception as e:
        print(f"Error when reading files: {e}")
        return []


def check_subfolder(directory, main_folder, first_run):
    # ----------------------------
    # Checking each file and folder within the folder that was set within the docker-compose file.
    # First run ignores files and just checks for folders.
    # Every other run then checks for files and subfolders.
    # If the file is new -> append it into an array of new files
    # If the file has changed cause of size or creation date -> append to list of changed files.
    # Deleted files will not get checked here, thats another function.
    # We are also saving the main folder, so the first folder we entered. This is so we know to which workspace the file will belong
    # ----------------------------
    try:
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
    except Exception as e:
        print(f"Error parsing {directory}: {str(e)} ")


def check_for_files_still_exist():
    # ----------------------------
    # We go through each file in the DB and check if the file is still there
    # ----------------------------
    try:
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
    except Exception as e:
        print(
            f"Error when checking for files from DB if they still exist in directory: {str(e)}"
        )
        return []


def add_files_to_anythingLLM(files_to_add):
    # -----------------------------
    # This function sends files to AnythingLLM via the api.
    # files_to_add has arrays of this structure: [file_path, main_folder, file_name]
    # We are going through each file and send them one by one to AnythingLLM
    # -----------------------------
    try:
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

                response = requests.post(
                    main_url + post_document_add_url,
                    headers=headers_files,
                    files=files,
                    timeout=30,  # Increased timeout for file uploads
                )

                doc_info = response.json()["documents"]
                location = doc_info[0][
                    "location"
                ]  # saving information of where it was saved within anythingLLM

                # create a folder with the same name as the base folder of the uploaded file
                response = requests.post(
                    main_url + create_folder_url,
                    headers=headers_json,
                    json={"name": folder_name},
                    timeout=10,
                )
                start = location.find("/") + 1
                only_file_name = location[start:]
                change_folder_json = {
                    "files": [
                        {"from": location, "to": f"{folder_name}/{only_file_name}"}
                    ]
                }

                # Request to move the file to new created folder
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
    except Exception as e:
        print(f"Error adding files to anythingLLM: {str(e)}")


def delete_files_from_anythingLLM(array_to_delete):
    # -----------------------------
    # This function deletes files from AnythingLLM, because they either got changed or deleted.
    # array_to_delete has arrays of this structure: [file_path, main_folder, file_name]
    # We are going through each file and delete them one by one in AnythingLLM
    # -----------------------------

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
    # -----------------------------
    # We are checking the files that got changed, deleting them from our DB and from AnythingLLM, then reuploading them.
    # files_that_changed has arrays of this structure: [file_path, main_folder, file_name]
    # -----------------------------

    try:
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
    except Exception as e:
        print(f"Error updaing files: {str(e)}")


def update_workspace_embeddings(list_of_new_embeddings):
    # -----------------------------
    # This function embeds the uploaded documents in the workspaces with 1 api call.
    # list_of_new_embeddings has arrays of this structure: [folder_name, only_file_name]
    # We go through every object and make a dict for each workspace that needs new embeddings.
    # Then we make an API call for each workspace to update the embeddings.
    # -----------------------------
    try:
        checked_workspaces = []
        workspaces_to_update = {}
        for new_workspace in list_of_new_embeddings:
            workspace_name = new_workspace[0]
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
                    print(
                        f" {workspace_name} did not exist as a workspace, so we create one"
                    )
                    new_workspace_json = {
                        "name": f"🔄{workspace_name}",
                        "similarityThreshold": 0.25,
                        "openAiTemp": 0.7,
                        "openAiHistory": 20,
                        "openAiPrompt": "Given the following conversation, relevant context, and a follow up question, reply with an answer to the current question the user is asking. Return only your response to the question given the above information following the users instructions as needed.",
                        "queryRefusalResponse": "There is no relevant information in this workspace to answer your query.",
                        "chatMode": "chat",
                        "topN": 4,
                    }

                    created_workspaces.objects.create(name=workspace_name)

                    response = requests.post(
                        url=main_url + new_workspace_url,
                        headers=headers_json,
                        json=new_workspace_json,
                        timeout=10,
                    )

            # now lets create the array which we will send to the API to update embeddings for the workspaces
            file_name = new_workspace[1]
            if workspace_name in workspaces_to_update:
                workspaces_to_update[workspace_name].append(
                    f"{workspace_name}/{file_name}"
                )
            else:
                workspaces_to_update[workspace_name] = [f"{workspace_name}/{file_name}"]

        for key, val in workspaces_to_update.items():
            json_to_send = {
                "adds": val,
                "deletes": [],
            }  # deletes is empty because we only delete files, which also deletes embeddings

            requests.post(
                url=main_url
                + get_workspace_url
                + key.replace(" ", "")
                + update_embeddings_url,
                headers=headers_json,
                json=json_to_send,
                timeout=10,
            )
    except Exception as e:
        print(f"Error updating embeddings: {str(e)}")


def delete_unused_workspaces():
    # -----------------------------
    # This function deletes workspaces with no documents embedded in them.
    # But only those workspaces get deleted, if they were created by this program and are in the database.
    # -----------------------------
    try:
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
            if len(workspace_data) != 0:
                this_workspace = workspace_data[0]
                if len(this_workspace["documents"]) == 0:
                    requests.delete(
                        url=main_url
                        + get_workspace_url
                        + str.lower(workspace.name).replace(" ", ""),
                        headers=headers_json,
                        timeout=10,
                    )
                    workspace.delete()
    except Exception as e:
        print(f"Error for deleting old workspaces {str(e)}")


def saveFile(file_path, main_folder):
    try:
        # First ensure any existing entries are removed
        FileInfo.objects.filter(
            filename=os.path.basename(file_path),
            absolute_path=os.path.abspath(file_path),
        ).delete()

        # Now create the new entry
        creation_time = os.path.getctime(file_path)
        modification_time = os.path.getmtime(file_path)
        found_created_at = timezone.make_aware(datetime.fromtimestamp(creation_time))
        found_modified_at = timezone.make_aware(
            datetime.fromtimestamp(modification_time)
        )

        return FileInfo.objects.create(
            filename=os.path.basename(file_path),
            absolute_path=os.path.abspath(file_path),
            main_folder=main_folder,
            file_size=os.path.getsize(file_path),
            created_at=found_created_at,
            modified_at=found_modified_at,
        )
    except Exception as e:
        print(f"Error saving files sources in DB {str(e)}")
