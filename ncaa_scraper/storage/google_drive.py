"""Google Drive integration for the NCAA scraper."""

import os
import pickle
import logging
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from ..config.constants import GOOGLE_DRIVE_SCOPES

logger = logging.getLogger(__name__)


class GoogleDriveManager:
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
            
            # Load existing token if available
            if os.path.exists(self.config.token_file):
                with open(self.config.token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Create credentials from environment variables
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
                
                # Save credentials for next run
                with open(self.config.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Successfully authenticated with Google Drive")
            return True
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Drive: {e}")
            return False
    
    def upload_file(self, file_path: str, folder_id: Optional[str] = None) -> Optional[str]:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Path to the file to upload
            folder_id: Optional Google Drive folder ID to upload to
        
        Returns:
            Google Drive file ID if successful, None if failed
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            file_metadata = {
                'name': os.path.basename(file_path),
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            logger.info(f"Successfully uploaded {file_path} to Google Drive. File ID: {file.get('id')}")
            return file.get('id')
            
        except Exception as e:
            logger.error(f"Failed to upload {file_path} to Google Drive: {e}")
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
                fields='id'
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
            
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
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
