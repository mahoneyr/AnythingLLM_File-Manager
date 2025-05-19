*Currently available as Version 0.9 (BETA)*

# AnythingLLM File Management Backend 🚀

A Django service that automatically syncs and manages files between your local filesystem and AnythingLLM. Just add files to your monitored folder and the system handles workspace organization and embedding automatically.

## Features ✨

- **File Monitoring** 📂: Watches for new, modified and deleted files
- **AnythingLLM Integration** 🔗:
  - 📤 Automatic file upload and updates
  - 🏢 Workspace management
  - ❌ Cleanup of deleted files
- **Image Processing** 🖼️:
  - 📷 AI-powered image descriptions using Ollama
  - 🔍 Text descriptions for better search
- **Scheduling** ⏳:
  - ⏰ Configurable CRON schedule
  - 📧 Manual updates via API endpoint and frontend

## Prerequisites 🛠️

- 🐳 Docker and Docker Compose
- 🧠 AnythingLLM instance (works with desktop and docker version)
- 🔑 Access to AnythingLLM Developer API
- 👁️ Optional: Ollama for image description functionality

## Configuration ⚙️

### Environment Variables 🌍

Quick config via `.env` file:

```
ANYTHING_LLM_API=your_api_key        # AnythingLLM API key
ANYTHING_LLM_URL=your_anything_llm_url  # URL without trailing /


USE_CRON=true                        # Enable scheduled checking
CHECK_FILES_CRON=*/1 * * * *         # Check every minute

# Image description (optional)
OLLAMA_URL=http://localhost:11434/api/generate
IMAGE_DESCRIPTION_ACTIVATE=true
IMAGE_DESCRIPTION_MODEL=gemma3:4b
IMAGE_DESCRIPTION_LANGUAGE=english

SORT_FILES=true                      # Auto-organize files
DELETE_UNUSED_FOLDERS=false          # Clean up empty folders
```

🔑 **API Key**: AnythingLLM Settings → Tools → Developer API → Generate New API Key  

### Folder Setup 📁

In `docker-compose.yml`, set your monitored directory:

```yaml
volumes:
  - C:\YOUR_FOLDER:/app/AnythingLLM
```
Make sure the path to your folder is before the `:/app/AnythingLLM`
📂 Each subfolder creates a matching workspace in AnythingLLM:
- `C:\MyFolder\Work` → **Work** workspace
- `C:\MyFolder\Personal` → **Personal** workspace

You can add as many monitored folders you need. If you want multiple, you can do it like this:
```yaml
volumes:
  - C:\YOUR_FOLDER:/app/AnythingLLM
  - C:\YOUR_SECOND_FOLDER:/app/AnythingLLM_SecondInstance
```
The programm checks for all folders which starts with "AnythingLLM" within the /app path. Meaning "AnythingLLM_Second", "AnythingLLMMyHoMewORK" and such all get detected. You can't use the same name multiple times tho.

Workspaces are automatically created and deleted to match your folder structure. 
⚠️ Files within the source folder (in this example the "C:\MyFolder") are skipped. Make sure you create subfolders, else the program can't create workspaces or upload files, as they are not detected.

## Image Description Feature 🖼️

Generates searchable text descriptions for images:

- 🔍 Detects images (.jpg, .png, etc.) in monitored folders
- 🧠 Uses Ollama for AI description
- 📄 Creates `.image_description` files
- 📤 Only uploads text descriptions for efficient embedding

**Setup**: Enable with `IMAGE_DESCRIPTION_ACTIVATE=true` and configure Ollama settings in `.env`

## File Sorting Feature 🗂️

⚠️ **BETA Feature**: Use with caution.

Automatically organizes documents into folders based on workspace associations:

- 🔍 Moves files to folders matching their workspace names
- 📁 Creates workspace folders as needed
- 🔄 Handles single and multi-workspace documents

**Configuration:**
- Enable with `SORT_FILES=true` in `.env`
- Optional: `DELETE_UNUSED_FOLDERS=true` to clean up empty folders

**Note:** Only needed if uploading through AnythingLLM Frontend, as this app already manages files automatically.

## Installation and Setup 🚀

1. **Clone the repository**:
```bash
git clone https://github.com/MrMarans/AnythingLLM_File-Manager.git
```

2. **Configure your environment**:
   - 🛠️ Copy the `.env.example` file, create an `.env` file and set your settings. 
   - 🔑 Set your API key, AnythingLLM URL, watched folder path
   - 📂 Configure docker-compose.yml with the correct volume mapping for your monitored directory

3. **Start the service**:
```bash
docker-compose up -d
```

🆙 **Updating to a new version or updating the configuration?** Use:
```bash
docker-compose down
docker-compose up -d --build
```

## How It Works 🛠️

1. **File Monitoring** 🔍:
   - Periodically checks the monitored directory based on the configured CRON schedule ⏳
   - Detects **new, modified, and deleted** files ✅
   - Maintains a database of detected files 🗃️

2. **AnythingLLM Integration** 🔗:
   - 📤 New files are automatically uploaded
   - 📝 Modified files trigger updates
   - ❌ Deleted files are removed
   - 🏢 Workspaces are created based on folder structure

3. **Image Processing** (when enabled) 🖼️:
   - 🔍 Detects image files in monitored directories
   - 🧠 Sends them to Ollama for description generation
   - 📝 Saves descriptions as separate files
   - 📤 Uploads only the text descriptions to AnythingLLM

4. **Workspace Management** 🏗️:
   - 📁 Creates workspaces automatically for new folders
   - 🔄 Updates embeddings when files change
   - 🧹 Removes empty workspaces to maintain cleanliness

## CRON Schedule Examples ⏰

You can modify the `CHECK_FILES_CRON` environment variable to adjust the checking frequency:

- `*/1 * * * *` - 🔄 Every minute (default)
- `0 */2 * * *` - ⏲️ Every 2 hours
- `0 9-17 * * 1-5` - ⏰ Every hour between 9 AM and 5 PM, Monday to Friday

To deactivate CRON Scheduler, set `USE_CRON=false` in the `.env` file


## Update via API

You can let the files manually update with a post request to the **ip:port/update_files/update/** endpoint.
For most people it will be **http://localhost:8000/update_files/update/**
Also available are: 
- **update_files/sort/**  for sorting files in folders 
- **update_files/clean/**  for deleting empty folders in AnythingLLM 
- **update_files/scan/**  to just check how many file updates there are
- **update_files/create_image_descriptions/** 


## Web UI Interface 🖥️ 🖱️

The application includes a simple web UI for managing your AnythingLLM files directly from your browser 🌐:

1. **How to access:** 🔗
   - Open your browser and navigate to the application's base URL (e.g., **http://localhost:8000/**)
   - You'll see a user-friendly dashboard with action buttons

2. **Available actions:** 🎮
   - 📤 **Full Upload and Cleaning** - Upload files and perform cleaning operations
   - 🗂️ **Sort Files** - Sort files into appropriate folders based on workspace associations
   - 🧹 **Clean Folders** - Delete unused folders
   - 🔍 **Scan Files** - Check for new, changed, or deleted files (doesn't upload anything)
   - 🖼️ **Create Image Descriptions** - Generate descriptions for all images

3. **Usage:** 👆
   - Simply click on the desired action button
   - The system will execute the requested operation
   - Results will be displayed in the response area below the buttons

This interface provides a convenient alternative to API calls or waiting for scheduled CRON jobs to run. 💫

## Troubleshooting 🛠️

Common issues and their solutions:

1. **Files not being detected** 🧐:
   - 🔍 Check the volume mounting in `docker-compose.yml`
   - 🔑 Verify file permissions
   - 📝 Check the logs for any errors

2. **AnythingLLM connection issues** 🔌:
   - ✅ Verify `ANYTHING_LLM_URL` is correct
   - 🔑 Ensure `ANYTHING_LLM_API` key is valid
   - 🌍 Check network connectivity

3. **Schedule not running** ⏳:
   - ✅ Verify `CHECK_FILES_CRON` format
   - 📜 Check container logs for scheduling errors
   - 🌍 Ensure the container has the correct timezone settings

4. **Image description not working** 🖼️:
   - ✅ Check Ollama is running and accessible
   - 🔍 Verify `OLLAMA_URL` is correct
   - 📝 Ensure the specified model is available in your Ollama instance

## Logs 📜

The service logs all operations and errors. Access the logs using:

```bash
docker-compose logs -f
```

## Support 🤝

For issues, questions, or contributions:
- 📝 Create an issue in the repository
- Make `VERBOSE` true in the .env file, this will print more logs
- 🛠️ Include logs and configuration details when reporting issues


## Upcoming Changes 🚀

- 📝 API documentation improvements
- 👤 Face Recognition Feature for Image Description
- 🎯 Check if filetype is supported by AnythingLLM
- Multiple Source Folder Paths
- 🚀 Much More exciting features!

- Version 1.0 will release with AnythingLLM Desktop Support, tested and working on Linux and Windows and granular API endpoints. No releasdate or window yet clear!

## Security Information 🔒

⚠️ **No security testing has been conducted. Use at your own risk.** This has not been tested for production. Please review the `settings.py` file and adjust as needed. You have been warned.

🔐 If you have security expertise, **pull requests with security improvements are welcome!**

## License 📜

MIT
