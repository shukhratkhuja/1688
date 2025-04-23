from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


def get_drive():
        # Auth
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("mycreds.txt")

    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
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
        print(f"📁 Folder '{folder_name}' already exists.")
        return folder_list[0]['id']
    
    # 2. Creating the folder
    folder_metadata = {
        'title': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    print(f"✅ Folder '{folder_name}' created.")
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


def upload_image_if_not_exists(images_folder_id, local_image_path):

    drive = get_drive()
    filename = local_image_path.split("/")[-1]

    query = f"title = '{filename}' and '{images_folder_id}' in parents and trashed = false"
    file_list = drive.ListFile({'q': query}).GetList()

    if file_list:
        print(f"🖼️ Image '{filename}' already exists.")
        return f"https://drive.google.com/uc?export=download&id={file_list[0]['id']}"
    
    file = drive.CreateFile({
        'title': filename,
        'parents': [{'id': images_folder_id}]
    })
    file.SetContentFile(local_image_path)
    file.Upload()

    file.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})

    print(f"✅ Image '{filename}' uploaded.")
    return f"https://drive.google.com/uc?export=download&id={file['id']}"


def upload_to_drive_and_get_link(gd_main_folder_id, local_filepath):

    drive = get_drive()

    direct_link = upload_or_update_file(drive=drive, folder_id=gd_main_folder_id, local_file_path=local_filepath)
    
    return direct_link
