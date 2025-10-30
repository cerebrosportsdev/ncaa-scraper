"""Google Drive integration for the NCAA scraper."""

import os
import pickle
import logging
from typing import Optional
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from ..config.constants import GOOGLE_DRIVE_SCOPES

logger = logging.getLogger(__name__)


class GoogleDriveManager:
    def delete_file_from_gdrive(self, file_id: str) -> bool:
        """
        Delete a file from Google Drive by its file ID.
        Args:
            file_id: The Google Drive file ID to delete
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return False
            self.service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
            logger.info(f"Deleted file from Google Drive: {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from Google Drive: {e}")
            return False
    """Manages Google Drive operations for the scraper."""
    
    def __init__(self, config):
        self.config = config
        self.service = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            creds = None

            # Prefer service account in non-interactive environments
            service_account_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            service_account_json_b64 = os.getenv('GOOGLE_CREDENTIALS_JSON_B64')
            credentials_file_path = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')

            # Allow base64-encoded JSON to avoid dotenv parsing issues
            if service_account_json_b64 and not service_account_json:
                try:
                    import base64
                    decoded = base64.b64decode(service_account_json_b64).decode('utf-8')
                    service_account_json = decoded
                except Exception as e:
                    logger.warning(f"Failed to decode GOOGLE_CREDENTIALS_JSON_B64: {e}")

            if service_account_json:
                try:
                    import json
                    sa_info = json.loads(service_account_json)
                    creds = ServiceAccountCredentials.from_service_account_info(sa_info, scopes=GOOGLE_DRIVE_SCOPES)
                    logger.info("Authenticated with Google Drive using service account from environment JSON")
                except Exception as e:
                    logger.warning(f"Failed to load service account from GOOGLE_CREDENTIALS_JSON: {e}")

            elif os.path.exists(credentials_file_path):
                try:
                    creds = ServiceAccountCredentials.from_service_account_file(credentials_file_path, scopes=GOOGLE_DRIVE_SCOPES)
                    logger.info("Authenticated with Google Drive using service account file credentials.json")
                except Exception as e:
                    logger.warning(f"Failed to load service account from {credentials_file_path}: {e}")

            if not creds:
                # Fallback to OAuth user flow (interactive) or refresh existing token
                if os.path.exists(self.config.token_file):
                    with open(self.config.token_file, 'rb') as token:
                        creds = pickle.load(token)

                if not creds or not creds.valid:
                    if creds and hasattr(creds, 'expired') and creds.expired and getattr(creds, 'refresh_token', None):
                        creds.refresh(Request())
                    else:
                        client_config = {
                            "installed": {
                                "client_id": self.config.google_client_id,
                                "client_secret": self.config.google_client_secret,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": [self.config.google_redirect_uri]
                            }
                        }
                        flow = InstalledAppFlow.from_client_config(client_config, GOOGLE_DRIVE_SCOPES)
                        creds = flow.run_local_server(port=0)

                    with open(self.config.token_file, 'wb') as token:
                        pickle.dump(creds, token)
            
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Successfully authenticated with Google Drive")
            return True
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Drive: {e}")
            return False
    
    def file_exists(self, file_name: str, folder_id: Optional[str] = None) -> Optional[str]:
        """
        Check if a file already exists in Google Drive.
        
        Args:
            file_name: Name of the file to check
            folder_id: Optional Google Drive folder ID to search in
        
        Returns:
            Google Drive file ID if exists, None if not found
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            # Search for existing file
            query = f"name='{file_name}' and trashed=false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, modifiedTime, size)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            files = results.get('files', [])
            
            if files:
                file_id = files[0]['id']
                modified_time = files[0].get('modifiedTime', 'Unknown')
                file_size = files[0].get('size', 'Unknown')
                logger.info(f"File already exists in Google Drive: {file_name} (ID: {file_id}, Modified: {modified_time}, Size: {file_size})")
                return file_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to check if file exists in Google Drive: {e}")
            return None
    
    def should_upload_file(self, file_path: str, folder_id: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Determine if a file should be uploaded based on existence and modification time.
        
        Args:
            file_path: Path to the local file
            folder_id: Optional Google Drive folder ID to check in
        
        Returns:
            Tuple of (should_upload, existing_file_id)
        """
        try:
            file_name = os.path.basename(file_path)
            existing_file_id = self.file_exists(file_name, folder_id)
            
            if not existing_file_id:
                return True, None
            
            # Check if local file is newer than Google Drive file
            if not os.path.exists(file_path):
                logger.warning(f"Local file {file_path} does not exist, skipping upload")
                return False, existing_file_id
            
            local_mtime = os.path.getmtime(file_path)
            
            try:
                # Get Google Drive file metadata
                file_metadata = self.service.files().get(
                    fileId=existing_file_id,
                    fields="modifiedTime, size",
                    supportsAllDrives=True
                ).execute()
                
                gdrive_modified = file_metadata.get('modifiedTime', '')
                if gdrive_modified:
                    from datetime import datetime
                    import pytz
                    
                    # Parse Google Drive timestamp
                    gdrive_time = datetime.fromisoformat(gdrive_modified.replace('Z', '+00:00'))
                    local_time = datetime.fromtimestamp(local_mtime, tz=pytz.UTC)
                    
                    if local_time > gdrive_time:
                        logger.info(f"Local file {file_name} is newer than Google Drive version, will update")
                        return True, existing_file_id
                    else:
                        logger.info(f"Google Drive file {file_name} is up to date, skipping upload")
                        return False, existing_file_id
                else:
                    # If we can't compare times, upload anyway
                    logger.info(f"Cannot compare modification times for {file_name}, will upload")
                    return True, existing_file_id
                    
            except Exception as e:
                logger.warning(f"Could not compare file timestamps for {file_name}: {e}")
                return True, existing_file_id
                
        except Exception as e:
            logger.error(f"Failed to determine if file should be uploaded: {e}")
            return True, None
    
    def upload_file(self, file_path: str, folder_id: Optional[str] = None, overwrite: bool = False) -> Optional[str]:
        """
        Upload a file to Google Drive with intelligent duplicate detection.
        
        Args:
            file_path: Path to the file to upload
            folder_id: Optional Google Drive folder ID to upload to
            overwrite: Whether to force overwrite existing files (ignores timestamp comparison)
        
        Returns:
            Google Drive file ID if successful, None if failed
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return None

            if not os.path.exists(file_path):
                logger.error(f"Local file {file_path} does not exist")
                return None

            file_name = os.path.basename(file_path)

            # Decide whether we should upload or update
            if not overwrite:
                should_upload, existing_file_id = self.should_upload_file(file_path, folder_id)
                if not should_upload:
                    return existing_file_id
            else:
                existing_file_id = self.file_exists(file_name, folder_id)

            # If an existing file is found and overwrite requested, call update_file which does NOT write parents
            if existing_file_id and overwrite:
                updated_id = self.update_file(existing_file_id, file_path)
                if updated_id:
                    logger.info(f"Successfully updated {file_path} in Google Drive. File ID: {updated_id}")
                return updated_id

            # If an existing file was found but overwrite not requested, create behavior handled earlier by should_upload
            if existing_file_id and not overwrite:
                # should_upload was True above, so proceed to update
                updated_id = self.update_file(existing_file_id, file_path)
                if updated_id:
                    logger.info(f"Successfully updated {file_path} in Google Drive. File ID: {updated_id}")
                return updated_id

            # No existing file -> create new file (include parents here)
            media = MediaFileUpload(file_path, resumable=True)
            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id',
                supportsAllDrives=True
            ).execute()
            logger.info(f"Successfully uploaded {file_path} to Google Drive. File ID: {file.get('id')}")
            return file.get('id')

        except Exception as e:
            logger.error(f"Failed to upload {file_path} to Google Drive: {e}")
            return None

    def create_file(self, local_path: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Create a new file in Drive under parent_id. Returns file id or None on failure."""
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            name = os.path.basename(local_path)
            media = MediaFileUpload(local_path, resumable=True)
            body = {'name': name}
            if parent_id:
                body['parents'] = [parent_id]
            file = self.service.files().create(body=body, media_body=media, supportsAllDrives=True, fields='id').execute()
            return file.get('id')
        except Exception as e:
            logger.error(f"Google Drive create error for {local_path}: {e}")
            return None

    def update_file(self, file_id: str, local_path: str) -> Optional[str]:
        """Update content of an existing Drive file. Important: do NOT include 'parents' in the update body.

        Returns file id on success or None on failure.
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            media = MediaFileUpload(local_path, resumable=True)
            file = self.service.files().update(fileId=file_id, media_body=media, supportsAllDrives=True, fields='id').execute()
            return file.get('id')
        except Exception as e:
            logger.error(f"Google Drive update error for {local_path} (fileId={file_id}): {e}")
            return None
    
    def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
        """
        Create a folder in Google Drive.
        
        Args:
            folder_name: Name of the folder to create
            parent_folder_id: Optional parent folder ID
        
        Returns:
            Google Drive folder ID if successful, None if failed
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id',
                supportsAllDrives=True
            ).execute()
            
            logger.info(f"Created Google Drive folder: {folder_name} (ID: {folder.get('id')})")
            return folder.get('id')
            
        except Exception as e:
            logger.error(f"Failed to create Google Drive folder {folder_name}: {e}")
            return None
    
    def find_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
        """
        Find existing folder in Google Drive.
        
        Args:
            folder_name: Name of the folder to find
            parent_folder_id: Optional parent folder ID
        
        Returns:
            Google Drive folder ID if found, None otherwise
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            files = results.get('files', [])
            
            if files:
                folder_id = files[0]['id']
                logger.info(f"Found existing Google Drive folder: {folder_name} (ID: {folder_id})")
                return folder_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find Google Drive folder {folder_name}: {e}")
            return None
    
    def find_or_create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
        """
        Find existing folder or create new one in Google Drive.
        
        Args:
            folder_name: Name of the folder to find/create
            parent_folder_id: Optional parent folder ID
        
        Returns:
            Google Drive folder ID if successful, None if failed
        """
        # Try to find existing folder first
        folder_id = self.find_folder(folder_name, parent_folder_id)
        if folder_id:
            return folder_id
        
        # Create new folder if not found
        return self.create_folder(folder_name, parent_folder_id)
    
    def create_folder_structure(self, year: str, month: str, gender: str, division: str, base_folder_id: Optional[str] = None) -> Optional[str]:
        """
        Create the organized folder structure: scraped_data/year/month/gender/division
        
        Args:
            year: Year (e.g., "2025")
            month: Month (e.g., "01")
            gender: Gender (e.g., "men", "women")
            division: Division (e.g., "d1", "d2", "d3")
            base_folder_id: Optional base folder ID to create structure under
        
        Returns:
            Final folder ID (gender/division level) if successful, None if failed
        """
        try:
            # Create scraped_data folder as the base
            scraped_data_folder_id = self.find_or_create_folder("scraped_data", base_folder_id)
            if not scraped_data_folder_id:
                return None
            
            # Create year folder under scraped_data
            year_folder_id = self.find_or_create_folder(year, scraped_data_folder_id)
            if not year_folder_id:
                return None
            
            # Create month folder under year
            month_folder_id = self.find_or_create_folder(month, year_folder_id)
            if not month_folder_id:
                return None
            
            # Create gender folder under month
            gender_folder_id = self.find_or_create_folder(gender, month_folder_id)
            if not gender_folder_id:
                return None
            
            # Create division folder under gender
            division_folder_id = self.find_or_create_folder(division, gender_folder_id)
            if not division_folder_id:
                return None
            
            return division_folder_id
            
        except Exception as e:
            logger.error(f"Failed to create Google Drive folder structure: {e}")
            return None
    
    def get_upload_stats(self, folder_id: Optional[str] = None) -> dict:
        """
        Get statistics about files in a Google Drive folder.
        
        Args:
            folder_id: Optional Google Drive folder ID to get stats for
        
        Returns:
            Dictionary with file statistics
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return {}
            
            query = "trashed=false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, size, modifiedTime, mimeType)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            files = results.get('files', [])
            
            stats = {
                'total_files': len(files),
                'total_size': 0,
                'csv_files': 0,
                'folders': 0,
                'files_by_type': {}
            }
            
            for file in files:
                mime_type = file.get('mimeType', '')
                file_size = int(file.get('size', 0))
                
                stats['total_size'] += file_size
                
                if mime_type == 'application/vnd.google-apps.folder':
                    stats['folders'] += 1
                elif mime_type == 'text/csv' or file.get('name', '').endswith('.csv'):
                    stats['csv_files'] += 1
                
                # Count by file extension
                file_name = file.get('name', '')
                if '.' in file_name:
                    ext = file_name.split('.')[-1].lower()
                    stats['files_by_type'][ext] = stats['files_by_type'].get(ext, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get upload stats: {e}")
            return {}
    
    def check_file_exists_in_gdrive(self, year: str, month: str, gender: str, division: str, day: str = None) -> tuple[bool, Optional[str]]:
        """
        Check if a file already exists in Google Drive for the given parameters.
        
        Args:
            year: Year (e.g., "2025")
            month: Month (e.g., "02")
            gender: Gender (e.g., "women")
            division: Division (e.g., "d3")
            day: Day (e.g., "06") - optional, if not provided checks for any file in the month
        
        Returns:
            Tuple of (exists, file_id)
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return False, None
            
            # Create folder structure to get the target folder ID
            folder_id = self.create_folder_structure(
                year, month, gender, division, self.config.google_drive_folder_id
            )
            
            if not folder_id:
                return False, None
            
            if day:
                # Check for specific day file
                file_name = f"basketball_{gender}_{division}_{year}_{month}_{day}.csv"
                existing_file_id = self.file_exists(file_name, folder_id)
                return existing_file_id is not None, existing_file_id
            else:
                # Check for any files in the month folder
                query = f"'{folder_id}' in parents and trashed=false and name contains 'basketball_{gender}_{division}_{year}_{month}'"
                results = self.service.files().list(
                    q=query,
                    fields="files(id, name)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()
                files = results.get('files', [])
                
                if files:
                    # Return the most recent file
                    file_id = files[0]['id']
                    logger.info(f"Found existing files in Google Drive for {gender} {division} {year}-{month}: {len(files)} files")
                    return True, file_id
                
                return False, None
                
        except Exception as e:
            logger.error(f"Failed to check Google Drive for existing files: {e}")
            return False, None
