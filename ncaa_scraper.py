#!/usr/bin/env python3
"""
NCAA Box Score Scraper
Automated scraper for NCAA basketball box scores
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from io import StringIO
import datetime
from datetime import timedelta
import argparse
import logging
import os
import pickle
import json
import requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Google Drive API configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Get configuration from environment variables
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'urn:ietf:wg:oauth:2.0:oob')
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'token.pickle')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def send_discord_notification(message, error_type="ERROR", division=None, date=None, gender=None, game_link=None):
    """
    Send a notification to Discord webhook
    
    Args:
        message (str): Message to send
        error_type (str): Type of notification (ERROR, WARNING, INFO)
        division (str): Division (d1, d2, d3)
        date (str): Date in YYYY-MM-DD format
        gender (str): Gender (men, women)
        game_link (str): Specific game link if applicable
    """
    if not DISCORD_WEBHOOK_URL:
        logger.debug("Discord webhook URL not configured, skipping notification")
        return
    
    try:
        # Choose emoji based on error type
        emoji_map = {
            "ERROR": "🚨",
            "WARNING": "⚠️", 
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "GAME_ERROR": "🏀"
        }
        emoji = emoji_map.get(error_type, "📢")
        
        # Build title with context
        title = f"{emoji} NCAA Scraper {error_type}"
        if division and gender:
            title += f" - {gender.title()} {division.upper()}"
        
        # Build description with context
        description = message
        fields = []
        
        if date:
            fields.append({
                "name": "📅 Date",
                "value": date,
                "inline": True
            })
        
        if division:
            fields.append({
                "name": "🏆 Division",
                "value": division.upper(),
                "inline": True
            })
        
        if gender:
            fields.append({
                "name": "⚽ Gender",
                "value": gender.title(),
                "inline": True
            })
        
        if game_link:
            fields.append({
                "name": "🔗 Game Link",
                "value": f"[View Game]({game_link})",
                "inline": False
            })
        
        # Create Discord embed
        embed = {
            "title": title,
            "description": description,
            "color": 0xff0000 if error_type == "ERROR" else 0xffaa00 if error_type == "WARNING" else 0x00ff00,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "footer": {
                "text": "NCAA Basketball Scraper"
            }
        }
        
        if fields:
            embed["fields"] = fields
        
        payload = {
            "embeds": [embed]
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        logger.debug(f"Discord notification sent successfully: {error_type}")
        
    except Exception as e:
        logger.error(f"Failed to send Discord notification: {e}")

def authenticate_google_drive():
    """
    Authenticate with Google Drive API using environment variables
    
    Returns:
        googleapiclient.discovery.Resource: Authenticated Google Drive service
    """
    creds = None
    
    # Check if required environment variables are set
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("Google Drive credentials not found in environment variables!")
        logger.error("Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file")
        logger.error("See config.env for an example configuration")
        return None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Create credentials from environment variables
            client_config = {
                "installed": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI]
                }
            }
            
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(file_path, folder_id=None):
    """
    Upload a file to Google Drive
    
    Args:
        file_path (str): Path to the file to upload
        folder_id (str): Optional Google Drive folder ID to upload to
    
    Returns:
        str: Google Drive file ID if successful, None if failed
    """
    try:
        service = authenticate_google_drive()
        if not service:
            return None
        
        file_metadata = {
            'name': os.path.basename(file_path),
        }
        
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        logger.info(f"Successfully uploaded {file_path} to Google Drive. File ID: {file.get('id')}")
        return file.get('id')
        
    except Exception as e:
        logger.error(f"Failed to upload {file_path} to Google Drive: {e}")
        return None

def create_drive_folder(folder_name, parent_folder_id=None):
    """
    Create a folder in Google Drive
    
    Args:
        folder_name (str): Name of the folder to create
        parent_folder_id (str): Optional parent folder ID
    
    Returns:
        str: Google Drive folder ID if successful, None if failed
    """
    try:
        service = authenticate_google_drive()
        if not service:
            return None
        
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        
        folder = service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        logger.info(f"Created Google Drive folder: {folder_name} (ID: {folder.get('id')})")
        return folder.get('id')
        
    except Exception as e:
        logger.error(f"Failed to create Google Drive folder {folder_name}: {e}")
        return None

def find_or_create_drive_folder(folder_name, parent_folder_id=None):
    """
    Find existing folder or create new one in Google Drive
    
    Args:
        folder_name (str): Name of the folder to find/create
        parent_folder_id (str): Optional parent folder ID
    
    Returns:
        str: Google Drive folder ID if successful, None if failed
    """
    try:
        service = authenticate_google_drive()
        if not service:
            return None
        
        # Search for existing folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"
        
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if files:
            # Folder exists, return its ID
            folder_id = files[0]['id']
            logger.info(f"Found existing Google Drive folder: {folder_name} (ID: {folder_id})")
            return folder_id
        else:
            # Folder doesn't exist, create it
            return create_drive_folder(folder_name, parent_folder_id)
            
    except Exception as e:
        logger.error(f"Failed to find/create Google Drive folder {folder_name}: {e}")
        return None

def create_drive_folder_structure(year, month, gender, division, base_folder_id=None):
    """
    Create the organized folder structure in Google Drive: scraped_data/year/month/gender/division
    
    Args:
        year (str): Year (e.g., "2025")
        month (str): Month (e.g., "01")
        gender (str): Gender (e.g., "men", "women")
        division (str): Division (e.g., "d1", "d2", "d3")
        base_folder_id (str): Optional base folder ID to create structure under
    
    Returns:
        str: Final folder ID (gender/division level) if successful, None if failed
    """
    try:
        # Create scraped_data folder as the base
        scraped_data_folder_id = find_or_create_drive_folder("scraped_data", base_folder_id)
        if not scraped_data_folder_id:
            return None
        
        # Create year folder under scraped_data
        year_folder_id = find_or_create_drive_folder(year, scraped_data_folder_id)
        if not year_folder_id:
            return None
        
        # Create month folder under year
        month_folder_id = find_or_create_drive_folder(month, year_folder_id)
        if not month_folder_id:
            return None
        
        # Create gender folder under month
        gender_folder_id = find_or_create_drive_folder(gender, month_folder_id)
        if not gender_folder_id:
            return None
        
        # Create division folder under gender
        division_folder_id = find_or_create_drive_folder(division, gender_folder_id)
        if not division_folder_id:
            return None
        
        return division_folder_id
        
    except Exception as e:
        logger.error(f"Failed to create Google Drive folder structure: {e}")
        return None

def game_exists_in_csv(csv_path, game_id):
    """
    Check if a game already exists in the CSV file
    
    Args:
        csv_path (str): Path to the CSV file
        game_id (str): Game ID to check for
    
    Returns:
        bool: True if game exists, False otherwise
    """
    if not os.path.exists(csv_path):
        return False
    
    try:
        df = pd.read_csv(csv_path)
        if 'GAMEID' in df.columns:
            return game_id in df['GAMEID'].values
        return False
    except Exception as e:
        logger.warning(f"Error reading CSV file {csv_path}: {e}")
        return False

def get_box_scores(link, output_dir=".", upload_to_gdrive=False, gdrive_folder_id=None, visited_links=None):
    """
    Scrape box scores from NCAA website
    
    Args:
        link (str): URL to the scoreboard page
        output_dir (str): Directory to save CSV files
        upload_to_gdrive (bool): Whether to upload to Google Drive
        gdrive_folder_id (str): Google Drive folder ID to upload to
        visited_links (set): Set of already visited game links to avoid duplicates
    """
    if visited_links is None:
        visited_links = set()
    link_indices = link.split('/')
    gender = link_indices[4]  # men or women
    division = link_indices[5]  # d1, d2, d3
    year = link_indices[6]     # 2025
    month = link_indices[7]    # 01, 02, etc.
    day = link_indices[8]      # 15, 21, etc.

    # print(gender, division, year, month, day)
    
    # Create year/month/gender/division folder structure
    date_dir = os.path.join(output_dir, year, month)
    gender_division_dir = os.path.join(date_dir, gender, division)
    os.makedirs(gender_division_dir, exist_ok=True)
    
    csv_name = os.path.join(gender_division_dir, f"basketball_{gender}_{division}_{year}_{month}_{day}.csv")
    
    # Check if this day's data already exists
    if os.path.exists(csv_name) and os.path.getsize(csv_name) > 0:
        logger.info(f"Data for {gender} {division} on {year}-{month}-{day} already exists, skipping...")
        return
    
    logger.info(f"Processing: {csv_name}")
    
    driver = webdriver.Chrome()
    try:
        # Navigate to the scoreboard page with Selenium to handle dynamic content
        logger.info(f"Loading scoreboard page: {link}")
        
        try:
            driver.get(link)
        except Exception as e:
            error_msg = f"Failed to load scoreboard page {link}: {e}"
            logger.error(error_msg)
            send_discord_notification(
                error_msg, 
                "ERROR", 
                division=division, 
                date=f"{year}-{month}-{day}", 
                gender=gender
            )
            return
        
        # Wait for the page to load and find game links
        wait = WebDriverWait(driver, 15)
        
        try:
            # Check if page loaded successfully by looking for common elements
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "gamePod-link")))
        except Exception as e:
            logger.warning(f"Scoreboard page may not exist or has no games for {link}: {e}")
            # Check for specific 404 error page
            try:
                # Check for the specific NCAA 404 error page
                error_404 = driver.find_elements(By.CLASS_NAME, "error-404")
                if error_404:
                    warning_msg = f"Page not found (404) - 'That's a foul on us...' error for {link}"
                    logger.warning(warning_msg)
                    send_discord_notification(
                        warning_msg, 
                        "WARNING", 
                        division=division, 
                        date=f"{year}-{month}-{day}", 
                        gender=gender
                    )
                    return
                elif "404" in driver.title or "not found" in driver.title.lower():
                    logger.warning(f"Page not found (404) for {link}")
                elif "error" in driver.title.lower():
                    logger.warning(f"Error page detected for {link}")
                else:
                    logger.warning(f"No games found on scoreboard page: {link}")
            except:
                logger.warning(f"Could not determine page status for {link}")
            return
        
        # Find all game links
        try:
            box_scores = driver.find_elements(By.CLASS_NAME, "gamePod-link")
            box_score_links = [box_score.get_attribute('href') for box_score in box_scores if box_score.get_attribute('href')]
        except Exception as e:
            logger.error(f"Error finding game links on {link}: {e}")
            return
        
        if not box_score_links:
            logger.warning(f"No valid game links found for {link}")
            return
        
        # Filter out already visited links
        new_links = [link for link in box_score_links if link not in visited_links]
        skipped_count = len(box_score_links) - len(new_links)
        
        if skipped_count > 0:
            logger.info(f"Found {len(box_score_links)} total games, {skipped_count} already visited, {len(new_links)} new games to scrape")
        else:
            logger.info(f"Found {len(box_score_links)} games to scrape")
        
        box_score_links = new_links
        for box_score_link in box_score_links:
            game_id = box_score_link.split('/')[-1]  # Extract game ID from URL
            
            # Check if this game link has already been visited in this session
            if box_score_link in visited_links:
                logger.info(f"Game link {box_score_link} already visited in this session, skipping...")
                continue
            
            # Check if this game already exists in the CSV
            if game_exists_in_csv(csv_name, game_id):
                logger.info(f"Game {game_id} already exists in {csv_name}, skipping...")
                continue
            
            # Add to visited links set
            visited_links.add(box_score_link)
            logger.info(f"Scraping: {box_score_link}")
            
            # Navigate to the game page
            try:
                driver.get(box_score_link)
                logger.info(f"Successfully navigated to: {box_score_link}")
            except Exception as e:
                error_msg = f"Failed to navigate to game page: {e}"
                logger.error(f"Failed to navigate to {box_score_link}: {e}")
                send_discord_notification(
                    error_msg, 
                    "GAME_ERROR", 
                    division=division, 
                    date=f"{year}-{month}-{day}", 
                    gender=gender, 
                    game_link=box_score_link
                )
                continue
            
            # Wait for the page to load completely
            wait = WebDriverWait(driver, 15)
            
            try:
                # Check if game page loaded successfully
                try:
                    # Wait for the team selector to be present
                    team_selector = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "boxscore-team-selector")))
                except Exception as e:
                    logger.warning(f"Box score page may not exist or is not available for {box_score_link}: {e}")
                    # Check for common error indicators
                    try:
                        if "404" in driver.title or "not found" in driver.title.lower():
                            logger.warning(f"Game page not found (404) for {box_score_link}")
                        elif "error" in driver.title.lower():
                            logger.warning(f"Error page detected for {box_score_link}")
                        elif "unavailable" in driver.page_source.lower():
                            logger.warning(f"Game data unavailable for {box_score_link}")
                        else:
                            logger.warning(f"Box score elements not found for {box_score_link}")
                    except:
                        logger.warning(f"Could not determine game page status for {box_score_link}")
                    continue
                
                # Get team selector elements
                try:
                    child_divs = team_selector.find_elements(By.TAG_NAME, "div")
                    
                    if len(child_divs) < 2:
                        logger.warning(f"Not enough team elements found for {box_score_link}")
                        continue
                        
                    child_divs_text = [div.text.strip() for div in child_divs if div.text.strip()]
                    
                    if len(child_divs_text) < 2:
                        logger.warning(f"Not enough team names found for {box_score_link}")
                        continue
                        
                except Exception as e:
                    logger.error(f"Error extracting team information from {box_score_link}: {e}")
                    continue

                # Wait for the boxscore table to be present
                try:
                    boxscore_table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'gamecenter-tab-boxscore')))
                    table = boxscore_table.find_element(By.TAG_NAME, 'table')
                except Exception as e:
                    logger.warning(f"Box score table not found for {box_score_link}: {e}")
                    continue

                # Parse first team's data
                try:
                    df_team_one = pd.read_html(StringIO(table.get_attribute('outerHTML')))[0]
                    
                    if df_team_one.empty:
                        logger.warning(f"Empty box score data for first team in {box_score_link}")
                        continue
                    
                    df_team_one['TEAM'] = child_divs_text[0]
                    df_team_one['OPP'] = child_divs_text[1]
                    df_team_one['GAMEID'] = game_id
                    df_team_one['GAMELINK'] = box_score_link
                    df_team_one = df_team_one.iloc[:-2]  # Remove last 2 rows
                    
                except Exception as e:
                    error_msg = f"Error parsing first team data: {e}"
                    logger.error(f"Error parsing first team data from {box_score_link}: {e}")
                    send_discord_notification(
                        error_msg, 
                        "GAME_ERROR", 
                        division=division, 
                        date=f"{year}-{month}-{day}", 
                        gender=gender, 
                        game_link=box_score_link
                    )
                    continue
                
                # Click to switch to second team
                try:
                    child_divs[1].click()
                    time.sleep(2)  # Wait for the switch
                except Exception as e:
                    logger.warning(f"Could not switch to second team for {box_score_link}: {e}")
                    continue

                # Get the second team's data
                try:
                    table = boxscore_table.find_element(By.TAG_NAME, 'table')
                    df_team_two = pd.read_html(StringIO(table.get_attribute('outerHTML')))[0]
                    
                    if df_team_two.empty:
                        logger.warning(f"Empty box score data for second team in {box_score_link}")
                        continue
                    
                    df_team_two['TEAM'] = child_divs_text[1]
                    df_team_two['OPP'] = child_divs_text[0]
                    df_team_two['GAMEID'] = game_id
                    df_team_two['GAMELINK'] = box_score_link
                    df_team_two = df_team_two.iloc[:-2]  # Remove last 2 rows
                    
                except Exception as e:
                    error_msg = f"Error parsing second team data: {e}"
                    logger.error(f"Error parsing second team data from {box_score_link}: {e}")
                    send_discord_notification(
                        error_msg, 
                        "GAME_ERROR", 
                        division=division, 
                        date=f"{year}-{month}-{day}", 
                        gender=gender, 
                        game_link=box_score_link
                    )
                    continue

                # Combine both teams into one dataframe
                try:
                    combined_df = pd.concat([df_team_one, df_team_two], ignore_index=True)
                    
                    if combined_df.empty:
                        logger.warning(f"Combined data is empty for {box_score_link}")
                        continue
                    
                    # Write to CSV (create file if it doesn't exist, append if it does)
                    file_exists = os.path.exists(csv_name)
                    combined_df.to_csv(csv_name, index=False, header=not file_exists, mode='a')
                    
                    logger.info(f"Successfully saved {len(combined_df)} rows to: {csv_name}")
                    
                except Exception as e:
                    error_msg = f"Error saving game data: {e}"
                    logger.error(f"Error saving data for {box_score_link}: {e}")
                    send_discord_notification(
                        error_msg, 
                        "GAME_ERROR", 
                        division=division, 
                        date=f"{year}-{month}-{day}", 
                        gender=gender, 
                        game_link=box_score_link
                    )
                    continue
                
            except Exception as e:
                error_msg = f"Unexpected error processing game: {e}"
                logger.error(f"Unexpected error processing {box_score_link}: {e}")
                send_discord_notification(
                    error_msg, 
                    "GAME_ERROR", 
                    division=division, 
                    date=f"{year}-{month}-{day}", 
                    gender=gender, 
                    game_link=box_score_link
                )
                continue
        
        # Upload the complete CSV file to Google Drive after all games are processed
        if upload_to_gdrive and os.path.exists(csv_name):
            logger.info(f"Uploading completed CSV for {gender} {division}: {csv_name}")
            
            # Create organized folder structure in Google Drive
            drive_folder_id = create_drive_folder_structure(year, month, gender, division, gdrive_folder_id)
            upload_to_drive(csv_name, drive_folder_id)
        elif upload_to_gdrive:
            logger.warning(f"CSV file not found for upload: {csv_name}")
                
    finally:
        driver.close()

def get_date_links(date_str=None):
    """
    Generate NCAA scoreboard links for a given date
    
    Args:
        date_str (str): Date in YYYY/MM/DD format. If None, uses yesterday.
    
    Returns:
        list: List of scoreboard URLs
    """
    try:
        if date_str is None:
            yesterday = datetime.date.today() - timedelta(days=1)
            date_str = yesterday.strftime('%Y/%m/%d')
        
        # Validate date format
        try:
            datetime.datetime.strptime(date_str, '%Y/%m/%d')
        except ValueError:
            logger.error(f"Invalid date format: {date_str}. Expected YYYY/MM/DD")
            return []
        
        links = [
            # f"https://www.ncaa.com/scoreboard/basketball-men/d1/{date_str}/all-conf",
            # f"https://www.ncaa.com/scoreboard/basketball-men/d2/{date_str}/all-conf",
            # f"https://www.ncaa.com/scoreboard/basketball-men/d3/{date_str}/all-conf",
            # f"https://www.ncaa.com/scoreboard/basketball-women/d1/{date_str}/all-conf",
            # f"https://www.ncaa.com/scoreboard/basketball-women/d2/{date_str}/all-conf",
            f"https://www.ncaa.com/scoreboard/basketball-women/d3/{date_str}/all-conf"
        ]
        return links
        
    except Exception as e:
        logger.error(f"Error generating date links: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description='NCAA Box Score Scraper')
    parser.add_argument('--date', type=str, help='Date in YYYY/MM/DD format (default: yesterday)')
    parser.add_argument('--output-dir', type=str, default='scraped_data', help='Output directory for CSV files')
    parser.add_argument('--backfill', action='store_true', help='Run backfill for specific dates')
    parser.add_argument('--upload-gdrive', action='store_true', help='Upload scraped data to Google Drive')
    parser.add_argument('--gdrive-folder-id', type=str, default=GOOGLE_DRIVE_FOLDER_ID, help='Google Drive folder ID to upload to (optional)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    logger.info(f"Output directory: {os.path.abspath(args.output_dir)}")
    
    # Create a set to track visited links across all scraping operations
    visited_links = set()
    
    try:
        if args.backfill:
            # Backfill specific dates
            backfill_dates = [
                "2025/01/12"
            ]
            
            for date in backfill_dates:
                logger.info(f"Backfilling data for {date}")
                links = get_date_links(date)
                if not links:
                    logger.error(f"No valid links generated for date {date}")
                    continue
                    
                for link in links:
                    try:
                        get_box_scores(link, args.output_dir, args.upload_gdrive, args.gdrive_folder_id, visited_links)
                    except Exception as e:
                        logger.error(f"Error processing backfill link {link}: {e}")
                        continue
        else:
            # Regular scraping for specified date or yesterday
            links = get_date_links(args.date)
            if not links:
                logger.error("No valid links generated for the specified date")
                return
                
            for link in links:
                try:
                    get_box_scores(link, args.output_dir, args.upload_gdrive, args.gdrive_folder_id, visited_links)
                except Exception as e:
                    logger.error(f"Error processing link {link}: {e}")
                    continue
        
        logger.info("Scraping completed!")
        
    except Exception as e:
        error_msg = f"Unexpected error in main function: {e}"
        logger.error(error_msg)
        send_discord_notification(error_msg, "ERROR")
        raise

if __name__ == "__main__":
    main()
