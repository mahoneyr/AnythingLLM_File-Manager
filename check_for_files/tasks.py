import os
import time
from datetime import datetime
import requests
from django.utils import timezone
from .models import FileInfo, TaskError, created_workspaces
from .describe_images import image_to_description
from pathlib import Path

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



# Get AnythingLLM API key and URL from environment variables
AnythingLLM_api = os.environ.get("ANYTHING_LLM_API")
if not AnythingLLM_api:
    raise ValueError("ANYTHING_LLM_API environment variable is not set")

main_url = os.environ.get("ANYTHING_LLM_URL")
if not main_url:
    raise ValueError("ANYTHING_LLM_URL environment variable is not set")

#this is just for testing
host_folder = os.environ.get("HOST_FOLDER")
if not host_folder:
    host_folder = "/app/AnythingLLM"
else:
    # Convert Windows path to Unix-style path for Docker
    host_folder = host_folder.replace("\\", "/")

image_description_activate = os.environ.get("IMAGE_DESCRIPTION_ACTIVATE", "false").lower() == "true"
if not image_description_activate:
    image_description_activate = False


# different urls parts for the API
get_workspaces_url = "/api/v1/workspaces"
get_documents_url = "/api/v1/documents"
delete_documents_url = "/api/v1/system/remove-documents"
post_document_add_url = "/api/v1/document/upload/"
create_folder_url = "/api/v1/document/create-folder"
move_to_folder_url = "/api/v1/document/move-files"
get_workspace_url = "/api/v1/workspace/"
update_embeddings_url = "/update-embeddings"
new_workspace_url = "/api/v1/workspace/new"
delete_folder_url = "/api/v1/document/remove-folder"

files_to_add = []
files_that_changed = []
update_embeddings = []

# header for all the get, post and delete requests which needs jsons.
headers_json = {
    "accept": "application/json",
    "Authorization": f"Bearer {AnythingLLM_api}",
    "Content-Type": "application/json",
}

class FileManager:
    def __init__(self):
        self.files_to_add = []
        self.files_that_changed = []
        self.update_embeddings = []

def anythingLLM_update():
    print(f"image_description_activate: {image_description_activate}")
    global files_to_add, files_that_changed, files_got_deleted  # Deklariere die Variablen als global
    files_to_add = []
    files_that_changed = []

    try:
        
        files_got_deleted = check_for_files_still_exist()
        print(f"start check_subfolder")
        check_subfolder(host_folder, host_folder, True)
        # Jetzt können Sie die globalen Variablen modifizieren
        files_to_add = remove_duplicates(files_to_add)
        files_got_deleted = remove_duplicates(files_got_deleted)
        files_that_changed = remove_duplicates(files_that_changed)
        
        print(f"Files to add: {files_to_add}")
        print(f"Files that changed: {files_that_changed}")
        print(f"Files got deleted: {files_got_deleted}")

        #if (
        #    len(files_got_deleted) == 0
        #    and len(files_to_add) == 0
        #    and len(files_that_changed) == 0
        #):
        #    print("Since no changes have been detected, nothing happens")
        #    TaskError.objects.create(success=True, error="Early stop cause no changes")
        #    return "Nothing to update"

        print(
            f"Found {len(files_to_add)} files to add, {len(files_that_changed)} files that changed and {len(files_got_deleted)} files that got deleted. Updating AnythingLLM now"
        )
        add_files_to_anythingLLM(files_to_add)

        delete_files_from_anythingLLM(files_got_deleted)

        update_files_in_anythingLLM(files_that_changed)


        update_workspace_embeddings(update_embeddings)
        
        delete_unused_workspaces()

        delete_unused_folders()
        print(
            f"Done Updating, task was successful. {len(FileInfo.objects.all())} documents in DB"
        )

        TaskError.objects.create(success=True, error=None)
        return f"Done Updating, task was successful. Found {len(files_to_add)} files to add, {len(files_that_changed)} files that changed and {len(files_got_deleted)} files that got deleted."
    except Exception as e:
        output = f"Error in task execution: {e}"
        print(output)
        TaskError.objects.create(success=False, error=str(e))
        return output

def remove_duplicates(list):
    seen_files = set()
    list = [
            file_info for file_info in list
            if tuple(file_info) not in seen_files and not seen_files.add(tuple(file_info))
        ]
    
    return list


def list_files(directory):
    # returning a list of all files within a path
    try:
        files = os.listdir(directory)
        return files
    except Exception as e:
        print(f"Error when reading files: {e}")
        return []


def Is_File_In_DB(file_name, file_path):
    print(f"Checking if file {file_name} in is in the DB")
    try:
        # Normalisiere den Pfad mit pathlib
        normalized_path = Path(file_path).resolve()
        file_info = FileInfo.objects.filter(
            filename=file_name, 
            absolute_path=str(normalized_path)
        ).first()
        
        if file_info is not None:  # Wenn ein Objekt gefunden wurde
            print(f"File {file_name} is in the DB")
            return file_info  # Gib das FileInfo Objekt zurück
        else:  # Wenn kein Objekt gefunden wurde (None)
            print(f"File {file_name} is not in the DB")
            return None
    except Exception as e:
        print(f"Error checking file in DB: {str(e)}")
        return None

def File_Changed(file_in_db, file_path):
    try:
        creation_time = os.path.getctime(file_path)
        modification_time = os.path.getmtime(file_path)

        found_file_size = os.path.getsize(file_path)
        found_created_at = timezone.make_aware(
            datetime.fromtimestamp(creation_time)
        )
        found_modified_at = timezone.make_aware(
            datetime.fromtimestamp(modification_time)
        )
        
        return (
            file_in_db.file_size != found_file_size
            or file_in_db.created_at < found_created_at
            or file_in_db.modified_at < found_modified_at
        )
    except Exception as e:
        print(f"Error checking if file changed: {str(e)}")
        return False

def file_in_db_or_updated(file_name, file_path, main_folder):
    file_info = Is_File_In_DB(file_name, file_path)
    if file_info is None:  # Wenn die Datei NICHT in der DB ist
        files_to_add.append([file_path, main_folder.lower().replace(" ", "-"), file_name])
    else:  # Wenn die Datei in der DB ist
        if File_Changed(file_info, file_path):
            files_that_changed.append([file_path, main_folder.lower().replace(" ", "-"), file_name])
            print(f"File {file_name} has changed.")
                

def check_subfolder(directory, main_folder, first_run):
    try:
        # Konvertiere den Eingabepfad in ein Path-Objekt
        directory_path = Path(directory)
        # Liste alle Dateien im Verzeichnis
        for file_path in directory_path.iterdir():
            file_name = file_path.name
            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')
            
            print(f"Checking file: {file_name} in directory: {directory}")
            if file_path.is_dir():
                check_subfolder(str(file_path), file_name, False)
                pass
            elif first_run:
                break
            elif file_name.lower().endswith(image_extensions) and image_description_activate:
                # Check if .image_description file exists
                description_file = file_path.with_suffix('.image_description')
                if description_file.exists():
                    continue
                description_path, worked = image_to_description(str(file_path))
                if worked:
                    file_in_db_or_updated(file_name, str(description_path), main_folder)
                else:
                    print(f"Error when creating image description for {file_name}: {description_path}")
                    continue
            else:
                file_in_db_or_updated(file_name, str(file_path), main_folder)
                            
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

            # Prüfe ob die Datei noch existiert
            if not os.path.exists(file_path):
                print(f"Skipping file {file_path} as it no longer exists")
                continue

            # Open and prepare the file for upload
            with open(file_path, "rb") as f:
                files = {
                    "file": (os.path.basename(file_path), f, "application/octet-stream")
                }
                print(f"Uploading file {file_path} to AnythingLLM: {main_url + post_document_add_url}")

                response = requests.post(
                    main_url + post_document_add_url + folder_name,
                    headers=headers_files,
                    files=files,
                    timeout=30,  # Increased timeout for file uploads
                    verify=False
                )
                if response.status_code != 200:
                    print(f"Error uploading file {file_path} to AnythingLLM: {response.json()}")
                    continue

                doc_info = response.json()["documents"]
                location = doc_info[0][
                    "location"
                ]  # saving information of where it was saved within anythingLLM

                if response.status_code == 200:
                    start = location.find("/") + 1
                    only_file_name = location[start:]
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
            main_url + get_documents_url, headers=headers_json, timeout=10, verify=False
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
                verify=False
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

def create_workspace_if_not_exists(workspace_name):
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

    print(f"Creating new workspace: {workspace_name}")
    response = requests.post(
        url=main_url + new_workspace_url,
        headers=headers_json,
        json=new_workspace_json,
        timeout=10,
        verify=False
    )

    print(f"Workspace {workspace_name} created, response: {response.json()}")


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
        for workspace in list_of_new_embeddings:
            workspace_name = workspace[0]
            if workspace_name not in checked_workspaces:  # check or create workspace
                response = requests.get(
                    url=main_url
                    + get_workspace_url
                    + workspace_name.lower().replace(" ", "-"),
                    headers=headers_json,
                    timeout=10,
                    verify=False
                )
                if len(response.json()["workspace"]) == 0:
                    create_workspace_if_not_exists(workspace_name)

            # now lets create the array which we will send to the API to update embeddings for the workspaces
            file_name = workspace[1]
            if workspace_name in workspaces_to_update:
                workspaces_to_update[workspace_name].append(
                    f"{workspace_name}/{file_name}"
                )
            else:
                workspaces_to_update[workspace_name] = [f"{workspace_name}/{file_name}"]
        print(f"Workspaces to update: {workspaces_to_update}")
        for key, val in workspaces_to_update.items():
            print(val)
            json_to_send = {
                "adds": val,
                "deletes": [],
            }  # deletes is empty because we only delete files, which also deletes embeddings
            requests.post(
                url=main_url
                + get_workspace_url
                + key.lower().replace(" ", "-")
                + update_embeddings_url,
                headers=headers_json,
                json=json_to_send,
                timeout=10,
                verify=False
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
                + str.lower(workspace.name).replace(" ", "-"),
                headers=headers_json,
                timeout=10,
                verify=False
            )
            workspace_data = response.json()["workspace"]
            if len(workspace_data) != 0:
                this_workspace = workspace_data[0]
                if len(this_workspace["documents"]) == 0:
                    requests.delete(
                        url=main_url
                        + get_workspace_url
                        + str.lower(workspace.name).replace(" ", "-"),
                        headers=headers_json,
                        timeout=10,
                        verify=False
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


def delete_unused_folders():
    # -----------------------------
    # This function deletes empty folders from AnythingLLM
    # -----------------------------
    try:
        response = requests.get(main_url + get_documents_url, headers=headers_json, timeout=10, verify=False)
        folders = response.json()["localFiles"]["items"]
        for folder in folders:
            
            if folder["name"] == "custom-documents": #we skip this basic folder since it always gets regenerated
                continue

            if folder["items"] == []:
                json_to_send = {
                    "name": folder["name"]
                }
                requests.delete(main_url + delete_folder_url, headers=headers_json, json=json_to_send, timeout=10, verify=False)
                print(f"Deleted folder: {folder['name']}")
    except Exception as e:
        print(f"Error deleting unused folders: {str(e)}")
    


if __name__ == "__main__":
    anythingLLM_update()