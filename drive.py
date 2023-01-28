import io
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

def google_api_service_creator(func):
    def wrapper(*args, **kwargs):
        # Authenticates and constructs service.
        service = GoogleDrive._get_service(
            api_name='drive',
            api_version='v3',
            scopes=[GoogleDrive.scope],
            key_file_location=GoogleDrive.key_file_location)
        result = func(service, *args, **kwargs)
        return result
    return wrapper

class GoogleDrive():

    scope = 'https://www.googleapis.com/auth/drive'
    key_file_location = 'google-drive-module/authtest-325214-f25670186971.json'

    @staticmethod
    def _get_service(api_name, api_version, scopes, key_file_location):
        """
        Get a service that communicates to a Google API.

        Args:
            api_name: The name of the api to connect to.
            api_version: The api version to connect to.
            scopes: A list auth scopes to authorize for the application.
            key_file_location: The path to a valid service account JSON key file.

        Returns:
            A service that is connected to the specified API.
        """
        credentials = service_account.Credentials.from_service_account_file(
        key_file_location)

        scoped_credentials = credentials.with_scopes(scopes)

        # Build the service object.
        service = build(api_name, api_version, credentials=scoped_credentials)

        return service

    @staticmethod
    @google_api_service_creator
    def list_files(service, folder_id: str = None, path: str = None, limit: int = None):
        """Prints the names, IDs, and paths of the files the user has access to.

        Args:
            service: Authenticated service instance of the GoogleAPI Client.
            folder_id: ID of the folder to list files from.
            path: Path of the folder to list files from.
            limit: Maximum number of files to list.

        Returns:
            None
        """
        try:
            query = ""
            if folder_id:
                query = f"'{folder_id}' in parents"
            elif path:
                query = f"mimeType='application/vnd.google-apps.folder' and trashed = false and fullText contains '{path}'"

            # Call the Drive v3 API
            results = service.files().list(q=query,fields="nextPageToken, files(id, name, parents, mimeType)").execute()
            items = results.get('files', [])

            if not items:
                print('No files found.')
                return
            print('Files:')
            for item in items:
                item['path'] = GoogleDrive.get_file_path(file_id=item['id'])
                print(item)
                if limit and len(items)>=limit:
                    break
            return items
        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')

    @staticmethod
    @google_api_service_creator
    def create_folder(service, folder_id: str = None, path: str = None):
        """Creates a folder under the given Folder ID or Path, and prints 
        new the folder ID.
        
        Args:
           service: Authenticated service instance of the GoogleAPI Client.

        Returns : 
            Folder Id.
        """
        try:
            # create drive api client
            file_metadata = {
                'name': 'Invoices',
                'mimeType': 'application/vnd.google-apps.folder'
            }

            # pylint: disable=maybe-no-member
            file = service.files().create(body=file_metadata, fields='id'
                                        ).execute()
            print(F'Folder ID: "{file.get("id")}".')
            return file.get('id')

        except HttpError as error:
            print(F'An error occurred: {error}')
            return None

    @staticmethod
    @google_api_service_creator
    def upload_to_folder(service, local_filepath: str, folder_id: str, path: str, filename: str):
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
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            media = MediaFileUpload(local_filepath,
                                    mimetype='application/pdf', resumable=True)
            # pylint: disable=maybe-no-member
            file = service.files().create(body=file_metadata, media_body=media,
                                        fields='id').execute()
            print(F'File ID: "{file.get("id")}".')
            return file.get('id')

        except HttpError as error:
            print(F'An error occurred: {error}')
            return None

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
                print(F'Download {int(status.progress() * 100)}.')

        except HttpError as error:
            print(F'An error occurred: {error}')
            file = None

        with open('drive_pdf.pdf', 'wb') as f:
            f.write(file.getvalue())
        return file.getvalue()

    def download_file_by_path(service, file_path: str, save_file: bool = False, local_save_path: str = ''):
        """Downloads a file based on file path.

        Args:
            service: Authenticated service instance of the GoogleAPI Client.
            file_path: path of the file to download.

        Returns:
            IO object with location.
        """

        try:
            query = "mimeType='application/pdf' and trashed = false and parents in '"+file_path+"'"
            results = service.files().list(q=query,fields="nextPageToken, files(id, name)").execute()
            items = results.get("files", [])

            if not items:
                print('No files found.')
                return None
            else:
                file_id = items[0]['id']
                request = service.files().get_media(fileId=file_id)
                file = io.BytesIO()
                downloader = MediaIoBaseDownload(file, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print(F'Download {int(status.progress() * 100)}.')
                
                if save_file:
                    with open(local_save_path, 'wb') as f:
                        f.write(file.getvalue())
        except HttpError as error:
            print(F'An error occurred: {error}')
            file = None

        return file.getvalue()

    @staticmethod
    @google_api_service_creator
    def get_file_path(service, file_id = '1hNV7wJrLQOBKPCwSQ0sPdSwKiW0ziauo', path='', name='', recursive_call: bool = False):
        file = service.files().get(fileId=file_id, fields='parents, name').execute()
        parents = file.get('parents')
        name = file.get('name') if not recursive_call else name
        if parents:
            parent_id = parents[0]
            parent_folder = service.files().get(fileId=parent_id, fields='name').execute()
            parent_name = parent_folder.get('name')
            path = parent_name + '/' + path
            return GoogleDrive.get_file_path(parent_id, path, name = name, recursive_call = True)
        else:
            if path == '':
                return file.get('name') if recursive_call else 'Shared/' + file.get('name')
            else:
                return path + name

if __name__ == '__main__':
    #create_folder(service=service)
    #upload_to_folder(service=service,folder_id='1pEJH86DPB9tn7P35j44vjVSATWdKk7IN')
    #print(GoogleDrive.get_file_path())
    GoogleDrive.list_files()
    #print(download_file(service=service, real_file_id='19C0uPItXL4OowN_j-9YEDGnF8aZ7ua7j'))

