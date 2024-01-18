import io
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


class GoogleDrive:
    scope = "https://www.googleapis.com/auth/drive"
    key_file_location = "credit-cards-automation-7034849bd49b.json"

    MY_DRIVE_FOLDER_ID = "0AFoAJwxmuRzuUk9PVA"
    ITEM_TYPES = {"folder": "application/vnd.google-apps.folder", "file": ""}

    # Decorators:

    def google_api_service_creator(func):
        def wrapper(*args, **kwargs):
            # Authenticates and constructs service.
            service = GoogleDrive._get_service(
                api_name="drive",
                api_version="v3",
                scopes=[GoogleDrive.scope],
                key_file_location=GoogleDrive.key_file_location,
            )
            result = func(service, *args, **kwargs)
            return result

        return wrapper

    def logging(func):
        def wrapper(*args, **kwargs):
            # Authenticates and constructs service.
            import logging

            # Set up the logger
            logger = logging.getLogger("Google Drive Module")
            logger.setLevel(logging.INFO)

            # Create a file handler
            """handler = logging.FileHandler('mylogfile.log')
            handler.setLevel(logging.INFO)"""

            # Create a console handler
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)

            # Create a formatter
            formatter = logging.Formatter(
                "%(name)s - %(asctime)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)

            # Add the handler to the logger
            logger.addHandler(handler)
            result = func(logger, *args, **kwargs)
            return result

        return wrapper

    # Private methods:

    @staticmethod
    def _get_service(api_name, api_version, scopes, key_file_location):
        """Get a service that communicates to a Google API.

        Args:
            api_name: The name of the api to connect to.
            api_version: The api version to connect to.
            scopes: A list auth scopes to authorize for the application.
            key_file_location: The path to a valid service account JSON key file.

        Returns:
            A service that is connected to the specified API.
        """
        credentials = service_account.Credentials.from_service_account_file(
            key_file_location
        )

        scoped_credentials = credentials.with_scopes(scopes)

        # Build the service object.
        service = build(api_name, api_version, credentials=scoped_credentials)

        return service

    def _calculate_path(
        child_parents,
        item_id=None,
        item_names=None,
        path_type="names",
        recursive_call=False,
        path="",
    ):
        if not recursive_call:
            path = item_id
        if item_id in child_parents.keys() and len(child_parents[item_id]) > 0:
            parent = child_parents[item_id][0]
            path = f"{parent}/{path}"
            return GoogleDrive._calculate_path(
                child_parents=child_parents,
                item_id=parent,
                item_names=item_names,
                path_type=path_type,
                recursive_call=True,
                path=path,
            )
        else:
            return (
                GoogleDrive._convert_id_path_to_name_path(path, item_names)
                if path_type == "names"
                else path
            )

    def _convert_id_path_to_name_path(path, item_names):
        names_path = ""
        parents = path.split("/")
        for parent in parents:
            names_path += f"{item_names[parent]}/"
        return names_path.rstrip("/")

    @staticmethod
    @logging
    @google_api_service_creator
    def get_files(
        service,
        logger,
        item_type: str = None,
        folder_id: str = None,
        path: str = None,
        limit: int = None,
        calculate_paths: bool = False,
    ):
        """Returns the names, IDs, and paths of the files the user has access to.

        Args:
            service: Authenticated service instance of the Google API Client.
            logger: Logger instance for Google Drive Module.
            item_type: Type of files allowed.
            folder_id: ID of the folder to list files from.
            path: Path of the folder to list files from.
            limit: Maximum number of files to list.

        Returns:
            None
        """
        try:
            logger.info("Starting get files process")

            # Structure validations
            if path and folder_id:
                raise Exception("Path and Folder ID cannot be set at the same time")

            # Applying query filters
            logger.info("Applying given filters")
            query = ""
            if not (calculate_paths or path):
                if folder_id:
                    query = f"'{folder_id}' in parents"
                if item_type:
                    if query:
                        query += " and "
                    if item_type.lower() in ["file", "files"]:
                        query += "mimeType != 'application/vnd.google-apps.folder'"
                    else:
                        query += f"mimeType = 'application/{'vnd.google-apps.folder' if item_type.lower() == 'folder' else item_type.lower()}'"

            # Call the Drive v3 API
            logger.info("Calling Drive API V3")
            results = (
                service.files()
                .list(
                    q=query, fields="nextPageToken, files(id, name, parents, mimeType)"
                )
                .execute()
            )
            items = results.get("files", [])
            if not items:
                logger.warning("No items found with the given parameters")
                return []
            logger.info(f"{str(len(items))} items found")

            # Preparing for path calculation
            if calculate_paths or path:
                logger.info("Preparing bases for path calculation")
                child_parents = {
                    item["id"]: item["parents"] if "parents" in item.keys() else []
                    for item in items
                }
                item_names = {item["id"]: item["name"] for item in items}
                item_names[GoogleDrive.MY_DRIVE_FOLDER_ID] = "My Drive"

                # Non query filters
                if folder_id:
                    items = [item for item in items if folder_id in item["parents"]]

                if item_type:
                    if item_type.lower() in ["file", "files"]:
                        items = [
                            item
                            for item in items
                            if item["mimeType"] != "application/vnd.google-apps.folder"
                        ]
                    else:
                        items = [
                            item
                            for item in items
                            if item["mimeType"]
                            == f"application/{'vnd.google-apps.folder' if item_type.lower() == 'folder' else item_type.lower()}"
                        ]

                for item in items:
                    item["type"] = (
                        "folder"
                        if item["mimeType"] == GoogleDrive.ITEM_TYPES.get("folder")
                        else "file"
                    )
                    item[
                        "path"
                    ] = f"{GoogleDrive._calculate_path(child_parents = child_parents, item_id = item['id'], item_names=item_names, path_type='names')}{'' if item['type'] == 'file' else '/'}"

                if path:
                    items = [item for item in items if item["path"].startswith(path)]

            logger.info("Calculating paths")
            logger.info("Infering item types")

            if limit and len(items) > limit:
                logger.info("Applying limit to the results")
                logger.info(
                    f"Filtering {len(items) - limit} results out of {len(items)}"
                )

                items = items[: limit if len(items) > limit else len(items)]

            logger.info("Get files process has successfuly finished")
            return items
        except Exception as error:
            logger.error("Get files process has failed")
            logger.error(f"Error message: {str(error)}")

    @staticmethod
    @google_api_service_creator
    def create_folder(service, folder_id: str = None, path: str = None):
        """
        Creates a folder under the given Folder ID or Path, and prints
        new the folder ID.

        Args:
           service: Authenticated service instance of the GoogleAPI Client.

        Returns :
            Folder Id.
        """
        try:
            # create drive api client
            file_metadata = {
                "name": "Invoices",
                "mimeType": "application/vnd.google-apps.folder",
            }

            # pylint: disable=maybe-no-member
            file = service.files().create(body=file_metadata, fields="id").execute()
            print(f'Folder ID: "{file.get("id")}".')
            return file.get("id")

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    @staticmethod
    @google_api_service_creator
    def upload_to_folder(
        service, local_filepath: str, folder_id: str, path: str, filename: str
    ):
        """Uploads a file to the specified folder and prints file ID, folder ID.

        Args:
            service: Authenticated service instance of the GoogleAPI Client.
            local_filepath: Local path of the file to be uploaded.
            folder_id: Id of the folder.
            filename: Name that the file will have once it's uploaded.

        Returns:
            ID of the file uploaded.
        """
        try:
            file_metadata = {"name": filename, "parents": [folder_id]}
            media = MediaFileUpload(
                local_filepath, mimetype="application/pdf", resumable=True
            )
            # pylint: disable=maybe-no-member
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            print(f'File ID: "{file.get("id")}".')
            return file.get("id")

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    @staticmethod
    @google_api_service_creator
    def upload_basic(service):
        """Insert new file.
        Returns : Id's of the file uploaded

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        try:
            file_metadata = {"name": "prueba.pdf"}
            media = MediaFileUpload("drive_pdf.pdf", mimetype="application/pdf")
            # pylint: disable=maybe-no-member
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            print(f'File ID: {file.get("id")}')

        except HttpError as error:
            print(f"An error occurred: {error}")
            file = None

        return file.get("id")

    @staticmethod
    @google_api_service_creator
    def download_file_by_id(service, file_id: str):
        """Downloads a file based on file ID.

        Args:
            service: Authenticated service instance of the GoogleAPI Client.
            file_id: ID of the file to download.

        Returns:
            IO object with location.
        """
        try:
            # pylint: disable=maybe-no-member
            request = service.files().get_media(fileId=file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}.")

        except HttpError as error:
            print(f"An error occurred: {error}")
            file = None

        with open("drive_pdf.pdf", "wb") as f:
            f.write(file.getvalue())
        return file.getvalue()

    def download_file_by_path(
        service, file_path: str, save_file: bool = False, local_save_path: str = ""
    ):
        """Downloads a file based on file path.

        Args:
            service: Authenticated service instance of the GoogleAPI Client.
            file_path: path of the file to download.

        Returns:
            IO object with location.
        """

        try:
            query = (
                "mimeType='application/pdf' and trashed = false and parents in '"
                + file_path
                + "'"
            )
            results = (
                service.files()
                .list(q=query, fields="nextPageToken, files(id, name)")
                .execute()
            )
            items = results.get("files", [])

            if not items:
                print("No files found.")
                return None
            else:
                file_id = items[0]["id"]
                request = service.files().get_media(fileId=file_id)
                file = io.BytesIO()
                downloader = MediaIoBaseDownload(file, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print(f"Download {int(status.progress() * 100)}.")

                if save_file:
                    with open(local_save_path, "wb") as f:
                        f.write(file.getvalue())
        except HttpError as error:
            print(f"An error occurred: {error}")
            file = None

        return file.getvalue()

    @staticmethod
    @google_api_service_creator
    def get_file_path(
        service,
        file_id="1hNV7wJrLQOBKPCwSQ0sPdSwKiW0ziauo",
        path="",
        name="",
        my_drive: bool = False,
        recursive_call: bool = False,
    ):
        file = service.files().get(fileId=file_id, fields="parents, name").execute()
        parents = file.get("parents")
        name = file.get("name") if not recursive_call else name
        if parents:
            parent_id = parents[0]
            parent_folder = (
                service.files().get(fileId=parent_id, fields="name").execute()
            )
            parent_name = parent_folder.get("name")
            path = parent_name + "/" + path
            return GoogleDrive.get_file_path(
                parent_id,
                path,
                name=name,
                my_drive=True if parent_id == GoogleDrive.MY_DRIVE_FOLDER_ID else False,
                recursive_call=True,
            )
        else:
            if path == "":
                return file.get("name")
            else:
                return path + name

    @staticmethod
    @google_api_service_creator
    def get_file_directory(
        service, file_id=None, path="", name="", my_drive: bool = False
    ):
        file = service.files().get(fileId=file_id, fields="parents, name").execute()
        parents = file.get("parents")
        if parents:
            parent_id = parents[0]
            parent_folder = (
                service.files().get(fileId=parent_id, fields="name").execute()
            )
            parent_name = parent_folder.get("name")
            path = parent_name + "/" + path
            return GoogleDrive.get_file_path(
                parent_id,
                path,
                name=name,
                my_drive=True if parent_id == GoogleDrive.MY_DRIVE_FOLDER_ID else False,
            )
        else:
            if path == "":
                return file.get("name")
            else:
                return path
    
    @logging
    @google_api_service_creator
    def download_file_content_bytes_by_id(service, logger, file_id: str):
        """Retrieves the file content as bytes using a streaming approach."""
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            logger.info("Download %d%%." % int(status.progress() * 100))

        fh.seek(0)  # Rewind the buffer to the beginning
        return fh.read()  # Read the entire file content into memory


if __name__ == "__main__":
    # create_folder(service=service)
    # GoogleDrive.upload_basic()
    # print(GoogleDrive.get_file_path())
    # GoogleDrive.download_file_by_id('1hNV7wJrLQOBKPCwSQ0sPdSwKiW0ziauo')
    # GoogleDrive.download_file_by_id(file_id='1kmrqadbgTa_fApL36zXcSpQvalDWsHLd')
    # print(download_file(service=service, real_file_id='19C0uPItXL4OowN_j-9YEDGnF8aZ7ua7j'))
    files = GoogleDrive.get_files(
        calculate_paths=True, path="Tarjetas de Crédito/1. VISA - Santander/", item_type="file"
    )
    print(len(files))
    for file in files:
        print(file)
