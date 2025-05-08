from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

import sys, time, os, random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.log_config import get_logger

logger = get_logger("GD", "app.log")

def get_drive():
    # Auth
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile("client_secrets.json")

    gauth.GetFlow()
    gauth.flow.params.update({
        'access_type': 'offline',
        'prompt': 'consent',
    })

    # ✅ Load saved credentials if available
    gauth.LoadCredentialsFile("mycreds.txt")

    if gauth.credentials is None:
        # No credentials, do manual authentication
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh credentials if expired
        gauth.Refresh()
    else:
        # Initialize the saved credentials
        gauth.Authorize()

    gauth.SaveCredentialsFile("mycreds.txt")

    drive = GoogleDrive(gauth)

    return drive


def get_or_create_folder(folder_name):

    drive = get_drive()
    # 1. Searching the folder
    query = f"title = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    folder_list = drive.ListFile({'q': query}).GetList()

    if folder_list:
        logger.info(f"📁 Folder '{folder_name}' already exists.")
        return folder_list[0]['id']
    
    # 2. Creating the folder
    folder_metadata = {
        'title': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    logger.info(f"✅ Folder '{folder_name}' created.")
    return folder['id']


def get_or_create_subfolder(parent_id, folder_name):

    drive = get_drive()

    query = f"title = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
    folder_list = drive.ListFile({'q': query}).GetList()

    if folder_list:
        return folder_list[0]['id']
    
    folder_metadata = {
        'title': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [{'id': parent_id}]
    }
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder['id']



def get_or_create_sub_subfolder(parent_id, folder_name):

    drive = get_drive()

    query = f"title = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
    folder_list = drive.ListFile({'q': query}).GetList()

    if folder_list:
        return folder_list[0]['id']
    
    folder_metadata = {
        'title': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [{'id': parent_id}]
    }
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder['id']



def upload_or_update_file(folder_id, local_file_path):
    
    drive = get_drive()
    filename = local_file_path.split("/")[-1]

    # 1. Searching the file from the folder
    query = f"title = '{filename}' and '{folder_id}' in parents and trashed = false"
    file_list = drive.ListFile({'q': query}).GetList()

    if file_list:
        # 🔁 File exists - updating the file
        file = file_list[0]
        file.SetContentFile(local_file_path)
        file.Upload()
        print(f"🔁 File '{filename}' updated.")
    else:
        # ➕ File not exists - creating the file
        file = drive.CreateFile({
            'title': filename,
            'parents': [{'id': folder_id}]
        })
        file.SetContentFile(local_file_path)
        file.Upload()
        print(f"✅ File '{filename}' created.")
    
    # Giving permissions
    file.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})

    # Direct download link
    file_id = file['id']

    return f"https://drive.google.com/uc?export=download&id={file_id}"



def upload_image_if_not_exists(gd_product_images_folder_id, local_image_path, max_retries=3):
    """
    Upload an image to Google Drive if it doesn't already exist.
    
    Args:
        images_folder_id (str): Google Drive folder ID for images
        local_image_path (str): Path to the local image file
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        str: Google Drive download URL or error message
    """
    drive = None
    logger = get_logger("GD", "app.log")
    
    # Validate inputs
    if not gd_product_images_folder_id or not local_image_path:
        logger.error("Missing required parameters")
        return "parameter_error"
        
    if not os.path.exists(local_image_path):
        logger.error(f"Local image does not exist: {local_image_path}")
        return "file_not_found"

    # Get filename from path
    try:
        filename = os.path.basename(local_image_path)
    except Exception as e:
        logger.error(f"Error extracting filename from path: {str(e)}")
        return "path_error"

    # Retry loop for Google Drive operations
    for attempt in range(max_retries):
        try:
            # Get authenticated drive instance
            drive = get_drive()
            
            # Search for existing file
            query = f"title = '{filename}' and '{gd_product_images_folder_id}' in parents and trashed = false"
            file_list = drive.ListFile({'q': query}).GetList()

            if file_list:
                logger.info(f"🖼️ Image '{filename}' already exists in Google Drive")
                return f"https://drive.google.com/uc?export=download&id={file_list[0]['id']}"
            
            # Upload new file
            file = drive.CreateFile({
                'title': filename,
                'parents': [{'id': gd_product_images_folder_id}]
            })
            file.SetContentFile(local_image_path)
            file.Upload()

            # Set public permission
            try:
                file.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})
            except Exception as e:
                logger.warning(f"Failed to set public permission: {str(e)}")
                # Continue anyway, as the file is uploaded

            logger.info(f"✅ Image '{filename}' uploaded to Google Drive")
            return f"https://drive.google.com/uc?export=download&id={file['id']}"
            
        except Exception as e:
            logger.error(f"Attempt {attempt+1}/{max_retries} failed: {str(e)}")
            
            # Exponential backoff
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Retrying after {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            
    # All retries failed
    logger.error(f"Failed to upload {filename} after {max_retries} attempts")
    return "upload_failed"


def upload_to_drive_and_get_link(gd_main_folder_id, local_filepath):

    direct_link = upload_or_update_file(folder_id=gd_main_folder_id, local_file_path=local_filepath)
    
    return direct_link
