# Google Drive Python Module

## Introduction

The Google Drive Python Module is a comprehensive library developed by Bruno Caracini to interact with the Google Drive API seamlessly. It offers functionalities to manage files and folders within Google Drive, making it an essential tool for applications requiring integration with Google's Drive storage services.

## Features

- **Authentication**: Utilizes OAuth2 authentication with service account credentials for secure server-to-server access to Google APIs.
- **File Operations**: Supports operations such as uploading files, creating folders, listing files, downloading files, and managing file metadata within Google Drive.

## Prerequisites

Before using the Google Drive Python Module, ensure that you have the following:

- **Google Cloud Platform (GCP) Project**: You need to have a GCP project set up where you can create a service account for authentication. If you don't have a GCP project, you can create one [here](https://console.cloud.google.com/projectcreate).

- **Service Account (SA)**: Create a service account within your GCP project. This service account will be used for authentication with the Google Drive API. Make sure to download the JSON key file associated with the service account, as it will be needed to authenticate the module.

- **File and Folder Sharing**: If you intend to access files or folders that are not owned by the service account, ensure that those files or folders are shared with the service account. This is necessary to grant the required permissions for reading, modifying, or deleting files and folders.

## Installation

To use the Google Drive Python Module in your project, follow these steps:

1. Install the required dependencies by running:

    ```bash
    pip install -r requirements.txt
    ```

2. Import the module into your Python script:

    ```python
    from google_drive import GoogleDrive
    ```

## Usage

### Authentication

Before using any functionalities of the module, ensure that you have set up OAuth2 authentication with a valid service account JSON key file. Set the path to the key file in your environment variables as `GOOGLE_DRIVE_KEY_FILE_LOCATION`.

### Example Usage

```python
from google_drive import GoogleDrive

# Get files with calculated paths
files = GoogleDrive.get_files(calculate_paths=True, item_type="files")
```

## Notes

- **Error Handling**: The module handles HTTP errors gracefully and logs them for troubleshooting purposes.
- **Scopes**: Ensure that the appropriate API scopes are configured for the desired functionalities. Modify the `scopes` dictionary in the module accordingly.

## Disclaimer

This module is a work in progress and may undergo changes and updates. Use with caution in production environments.

## Contributing

Contributions to the Google Drive Python Module are welcome! If you encounter any issues or have suggestions for improvements, feel free to open an issue or submit a pull request on the GitHub repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author

This module was authored by [Bruno Caracini](https://github.com/brunocaracini).

📁 Manage your files effortlessly with Google Drive integration! 🚀