# AnythingLLM File Management Backend

A Django-based backend service that automatically manages file synchronization between a local directory and AnythingLLM. This service monitors file changes, handles uploads, updates, and deletions, while managing workspaces in AnythingLLM.

## Features

- **Automated File Monitoring**: Continuously monitors a specified directory for:
  - New files
  - Modified files
  - Deleted files
- **AnythingLLM Integration**:
  - Automatic file upload to AnythingLLM
  - File updates when content changes
  - Removal of deleted files
  - Workspace management (creation and cleanup)
- **Smart Workspace Management**:
  - Automatic workspace creation based on folder structure
  - Cleanup of empty workspaces
  - Embedding updates for modified content
- **Configurable Scheduling**:
  - Customizable monitoring frequency via CRON configuration
  - Default checking interval: every minute

## Prerequisites

- Docker and Docker Compose
- AnythingLLM instance
- Access to AnythingLLM Developer API

## Configuration

### Environment Variables

Configure the service using the following environment variables in your `docker-compose.yml`:

```yaml
environment:
  - ANYTHING_LLM_API=your_api_key
  - ANYTHING_LLM_URL=your_anything_llm_url
  - CHECK_FILES_CRON=*/1 * * * *  # CRON schedule for file checking
```

### Volume Configuration

Specify the directory to monitor in the `docker-compose.yml`:

```yaml
volumes:
  - /your/local/path/:/app/AnythingLLM
```

The program will go through every folder within the folder you set.
Meaning, if set the folder to
C:\MyAnythingLLM_folder\
then the programm will check all folders and subfolders within this folder.
For each folder within that path there will be a workspace and folder created in AnythingLLM. (As you can't create subfolders in AnythingLLM, those get ignored too).

Example:
C:\MyAnythingLLM_folder\Homework
C:\MyAnythingLLM_folder\Contracts
C:\MyAnythingLLM_folder\ActualHomework
Will create the Workspaces Homework, Contracts and ActualHomework.

Those workspaces also get deleted when the local folders are deleted.

## Installation and Setup

1. Clone the repository:
```bash
git clone [repository-url]
```

2. Configure your environment:
   - Change the example docker-compose.yml
   - Adjust the environment variables like developer API and AnythingLLM URL
   - Set the correct volume mapping for your monitored directory

3. Start the service:
```bash
docker-compose up -d
```

## Docker Compose Configuration

Example configuration:

```yaml
services:
  web:
    build:
      context: .
    container_name: any_folder
    image: any_folder
    volumes:
      - static_volume:/app/static
      - storage_volume:/app/storage
      - database_volume:/app/database
      - /your/local/path:/app/AnythingLLM
    environment:
      - DJANGO_SETTINGS_MODULE=main.settings
      - PYTHONPATH=/app
      - DATABASE_DIR=/app/database
      - STORAGE_DIR=/app/storage
      - PORT=8010
      - ANYTHING_LLM_API=your_api_key
      - ANYTHING_LLM_URL=your_anything_llm_url
      - CHECK_FILES_CRON=*/1 * * * *
```

## How It Works

1. **File Monitoring**:
   - The service periodically checks the monitored directory based on the configured CRON schedule
   - Detects new, modified, and deleted files
   - Maintains a database of known files

2. **AnythingLLM Integration**:
   - New files are automatically uploaded to AnythingLLM
   - Modified files trigger updates in AnythingLLM
   - Deleted files are removed from AnythingLLM
   - Workspaces are created based on folder structure

3. **Workspace Management**:
   - Creates workspaces automatically for new folders
   - Updates embeddings when files change
   - Removes empty workspaces to maintain cleanliness

## CRON Schedule Examples

You can modify the CHECK_FILES_CRON environment variable to adjust the checking frequency:

- `*/1 * * * *` - Every minute (default)
- `*/5 * * * *` - Every 5 minutes
- `0 * * * *` - Every hour
- `0 */2 * * *` - Every 2 hours
- `0 9-17 * * 1-5` - Every hour between 9 AM and 5 PM, Monday to Friday

## Troubleshooting

Common issues and their solutions:

1. **Files not being detected**:
   - Check the volume mounting in docker-compose.yml
   - Verify file permissions
   - Check the logs for any errors

2. **AnythingLLM connection issues**:
   - Verify the ANYTHING_LLM_URL is correct
   - Ensure the ANYTHING_LLM_API key is valid
   - Check network connectivity

3. **Schedule not running**:
   - Verify the CHECK_FILES_CRON format
   - Check the container logs for scheduling errors
   - Ensure the container has the correct timezone settings

## Logs

The service logs all operations and errors. Access the logs using:

```bash
docker-compose logs -f
```

## Support

For issues, questions, or contributions, please:
- Create an issue in the repository
- Ensure logs and configuration details are included when reporting issues

## Known Issues:
- While we can create new Workspaces and delete them, we can only create new folders. So deleting folders needs to first be possible through the AnythingLLM API so I can add this feature.

## Upcoming changes:
- Improving code
- Adding option for a workspace.json file of some sort to set the settings of a workspace by changing the json.

## License

MIT
