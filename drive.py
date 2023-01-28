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
    key_file_location = 'authtest-325214-395d7e2e3db1.json'

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
        key_file_location)

        scoped_credentials = credentials.with_scopes(scopes)

        # Build the service object.
        service = build(api_name, api_version, credentials=scoped_credentials)

        return service

    @staticmethod
    @google_api_service_creator
    def list_files(service):
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """


        try:

            # Call the Drive v3 API
            results = service.files().list().execute()
            items = results.get('files', [])

            if not items:
                print('No files found.')
                return
            print('Files:')
            for item in items:
                print(u'{0} ({1})'.format(item['name'], item['id']))
        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')

    @staticmethod
    @google_api_service_creator
    def create_folder(service):
        """ Create a folder and prints the folder ID
        Returns : Folder Id

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
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
    def upload_to_folder(service,folder_id):
        """Upload a file to the specified folder and prints file ID, folder ID
        Args: Id of the folder
        Returns: ID of the file uploaded

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """

        try:

            file_metadata = {
                'name': 'Albero Genealogico - FAMIGLIA CARACINI.pdf',
                'parents': [folder_id]
            }
            media = MediaFileUpload('Albero Genealogico - FAMIGLIA CARACINI.pdf',
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
    def download_file(service, real_file_id):
        """Downloads a file
        Args:
            real_file_id: ID of the file to download
        Returns : IO object with location.

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """

        try:
            # create drive api client
            file_id = real_file_id

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


if __name__ == '__main__':
    #create_folder(service=service)
    #upload_to_folder(service=service,folder_id='1pEJH86DPB9tn7P35j44vjVSATWdKk7IN')
    GoogleDrive.list_files()
    #print(download_file(service=service, real_file_id='19C0uPItXL4OowN_j-9YEDGnF8aZ7ua7j'))

