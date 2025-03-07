# AnythingLLM File Management Backend 🚀

A Django-based backend service that automatically manages file synchronization between a local directory and AnythingLLM. This service monitors file changes, handles uploads, updates, and deletions, while managing workspaces in AnythingLLM.

## Features ✨

- **Automated File Monitoring** 📂: Continuously monitors a specified directory for:
  - ✅ New files
  - 🔄 Modified files
  - 🗑️ Deleted files
- **AnythingLLM Integration** 🔗:
  - 📤 Automatic file upload to AnythingLLM
  - 📝 File updates when content changes
  - ❌ Removal of deleted files
  - 🏢 Workspace management (creation and deletion)
  - ⚠️ Only deleting workspaces created by this backend! No workspaces created via the AnythingLLM UI will be removed.
- **Smart Workspace Management** 🏗️:
  - 📁 Automatic workspace creation based on folder structure
  - 🧹 Cleanup of empty workspaces (when created by this software)
  - 🔄 Embedding updates for modified content
- **Configurable Scheduling** ⏳:
  - 🛠️ Customizable monitoring frequency via CRON configuration (set how often it looks for changes based on time)
  - ⏰ Default checking interval: every minute
  - 📧 Custom updates with a post request to **/update_files/update/**

## Prerequisites 🛠️

- 🐳 Docker and Docker Compose
- 🧠 AnythingLLM instance (works with desktop and docker version)
- 🔑 Access to AnythingLLM Developer API

## Configuration ⚙️

### Environment Variables 🌍

Configure the service using the following environment variables in your `docker-compose.yml`:

```yaml
environment:
  - ANYTHING_LLM_API=your_api_key
  - ANYTHING_LLM_URL=your_anything_llm_url
  - USE_CRON=true #activates time based checks
  - CHECK_FILES_CRON=*/1 * * * *  # CRON schedule for file checking
```

🔑 You can find the developer API Key here: **AnythingLLM Settings -> Tools -> Developer API -> Generate New API Key**
🌍 You can get the URL from the Developer API Window -> Click on **"Read the API documentation"** -> Example URL: `http://192.168.80.35:3001/api/docs/` -> Use `http://192.168.80.35:3001` without a trailing `/`

### Volume Configuration 📁

Specify the directory to monitor in `docker-compose.yml`:

```yaml
volumes:
  - C:\YOUR_PATH:/app/AnythingLLM
```

📂 The program will scan every folder within the specified path.

Example:
- `C:\MyAnythingLLM_folder\Homework`
- `C:\MyAnythingLLM_folder\Contracts`
- `C:\MyAnythingLLM_folder\ActualHomework`

Will create the Workspaces:
- **Homework**
- **Contracts**
- **ActualHomework**

🗑️ These workspaces also get deleted when the local folders are removed.

## Installation and Setup 🚀

1. **Clone the repository**:
```bash
git clone https://github.com/MrMarans/AnythingLLM_File-Manager.git
```

2. **Configure your environment**:
   - 🛠️ Modify `docker-compose.yml`
   - 🔑 Adjust environment variables (API key, AnythingLLM URL, watched folder path)
   - 📂 Set correct volume mapping for your monitored directory

3. **Start the service**:
```bash
docker-compose up -d
```

🆙 **Updating to a new version or updating the docker-compose file?** Use:
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

3. **Workspace Management** 🏗️:
   - 📁 Creates workspaces automatically for new folders
   - 🔄 Updates embeddings when files change
   - 🧹 Removes empty workspaces to maintain cleanliness

## CRON Schedule Examples ⏰

You can modify the `CHECK_FILES_CRON` environment variable to adjust the checking frequency:

- `*/1 * * * *` - 🔄 Every minute (default)
- `*/5 * * * *` - ⏳ Every 5 minutes
- `0 * * * *` - 🕒 Every hour
- `0 */2 * * *` - ⏲️ Every 2 hours
- `0 9-17 * * 1-5` - ⏰ Every hour between 9 AM and 5 PM, Monday to Friday

To deactivate CRON Scheduler, set `USE_CRON=false` in the `docker-compose.yml`

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

## Logs 📜

The service logs all operations and errors. Access the logs using:

```bash
docker-compose logs -f
```

## Support 🤝

For issues, questions, or contributions:
- 📝 Create an issue in the repository
- 🛠️ Include logs and configuration details when reporting issues

## Known Issues ⚠️

- ⚠️ While we can **create new Workspaces and delete them**, we can only **create new folders**.
  - **Folder deletion is not yet supported** via the AnythingLLM API. This will be added once supported.

## Upcoming Changes 🚀

- 🛠️ Code improvements
- 📜 Adding an option for a `workspace.json` file to configure workspace settings

## Security Information 🔒

⚠️ **No security testing has been conducted. Use at your own risk.** This has not been tested for production. Please review the `settings.py` file and adjust as needed.

🔐 If you have security expertise, **pull requests with security improvements are welcome!**

## License 📜

MIT
