"""NCAA-specific scraper implementation."""

import time
import logging
from typing import List, Optional, Set
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from io import StringIO
import pandas as pd

from .base_scraper import BaseScraper
from .selenium_utils import SeleniumUtils
from ..models import GameData, TeamData
from ..utils import parse_url_components, extract_game_id_from_url
from ..config.constants import ErrorType

logger = logging.getLogger(__name__)


class NCAAScraper(BaseScraper):
    """NCAA basketball box score scraper."""
    
    def __init__(self, config):
        super().__init__(config)
        self.driver: Optional[webdriver.Chrome] = None
    
    def scrape(self, url: str) -> List[GameData]:
        """
        Scrape NCAA box scores from a scoreboard URL.
        Args:
            url: NCAA scoreboard URL
        Returns:
            List of scraped game data
        """
        try:
            # Parse URL components
            components = parse_url_components(url)
            year = components['year']
            month = components['month']
            day = components['day']
            gender = components['gender']
            division = components['division']
            csv_path = self.file_manager.get_csv_path(year, month, day, gender, division)

            # Track all game IDs for this date/gender across divisions in memory only
            if not hasattr(self, '_scrape_session_game_ids'):
                self._scrape_session_game_ids = {}
            session_key = f"{year}_{month}_{day}_{gender}"
            if session_key not in self._scrape_session_game_ids:
                self._scrape_session_game_ids[session_key] = {}
            all_game_ids = self._scrape_session_game_ids[session_key]

            # Always overwrite local file if it exists
            if self.file_manager.file_exists_and_has_content(csv_path):
                try:
                    import os
                    os.remove(csv_path)
                    self.logger.info(f"Existing local file {csv_path} deleted for overwrite.")
                except Exception as e:
                    self.logger.warning(f"Could not delete local file {csv_path}: {e}")
            # Always overwrite Google Drive file if it exists
            if self.config.upload_to_gdrive:
                gdrive_exists, gdrive_file_id = self.google_drive.check_file_exists_in_gdrive(
                    year, month, gender, division, day
                )
                if gdrive_exists and gdrive_file_id:
                    try:
                        self.google_drive.delete_file_from_gdrive(gdrive_file_id)
                        self.logger.info(f"Existing Google Drive file for {gender} {division} {year}-{month}-{day} deleted for overwrite.")
                    except Exception as e:
                        self.logger.warning(f"Could not delete Google Drive file: {e}")
            self.logger.info(f"Processing: {csv_path}")
            # Initialize driver with retry mechanism
            try:
                self.driver = SeleniumUtils.create_driver(headless=True, max_retries=3)
            except Exception as e:
                error_msg = f"Failed to initialize WebDriver: {e}"
                self.logger.error(error_msg)
                self.send_notification(
                    error_msg,
                    ErrorType.ERROR,
                    division=division,
                    date=f"{year}-{month}-{day}",
                    gender=gender
                )
                return []
            try:
                # Load scoreboard page
                if not self._load_scoreboard_page(url, division, gender, f"{year}-{month}-{day}"):
                    return []
                # Get game links
                game_links = self._extract_game_links()
                if not game_links:
                    no_links_msg = f"No valid game links found for {url}"
                    self.logger.warning(no_links_msg)
                    self.send_notification(
                        no_links_msg,
                        ErrorType.INFO,
                        division=division,
                        date=f"{year}-{month}-{day}",
                        gender=gender
                    )
                    return []
                self.logger.info(f"Found {len(game_links)} games to scrape for {division}")
                scraped_games = []
                new_game_ids = set()
                for game_link in game_links:
                    try:
                        game_data = self._scrape_single_game(
                            game_link, year, month, day, gender, division, csv_path
                        )
                        if game_data:
                            # Mark duplicate if game_id already in all_game_ids
                            is_duplicate = game_data.game_id in all_game_ids
                            df = game_data.to_combined_dataframe()
                            # Add DUPLICATE_ACROSS_DIVISIONS column: TRUE for duplicates, empty for non-duplicates
                            df["DUPLICATE_ACROSS_DIVISIONS"] = "TRUE" if is_duplicate else ""
                            # Always reorder columns so DUPLICATE_ACROSS_DIVISIONS is last
                            cols = list(df.columns)
                            if "DUPLICATE_ACROSS_DIVISIONS" in cols:
                                cols = [c for c in cols if c != "DUPLICATE_ACROSS_DIVISIONS"] + ["DUPLICATE_ACROSS_DIVISIONS"]
                                df = df[cols]
                            import os
                            write_header = not os.path.exists(csv_path)
                            if write_header:
                                df.to_csv(csv_path, index=False, header=True, mode='w')
                            else:
                                import pandas as pd
                                try:
                                    existing = pd.read_csv(csv_path, nrows=0)
                                    df = df[existing.columns.tolist()]
                                except Exception:
                                    pass
                                df.to_csv(csv_path, index=False, header=False, mode='a')
                            scraped_games.append(game_data)
                            new_game_ids.add(game_data.game_id)
                            # Retroactively update previous division files for this game_id
                            for div, path in all_game_ids.get(game_data.game_id, {}).items():
                                try:
                                    import pandas as pd
                                    # Try standard read, fallback to python engine if tokenization errors occur
                                    try:
                                        prev_df = pd.read_csv(path)
                                    except Exception:
                                        try:
                                            prev_df = pd.read_csv(path, engine='python', sep=',', on_bad_lines='skip')
                                        except Exception as e:
                                            self.logger.warning(f"Could not parse previous CSV {path} for duplicate update: {e}")
                                            continue

                                    if "DUPLICATE_ACROSS_DIVISIONS" not in prev_df.columns:
                                        prev_df["DUPLICATE_ACROSS_DIVISIONS"] = ""
                                    # Ensure string dtype to avoid pandas dtype warnings when assigning 'TRUE'
                                    # Replace NaN with empty string and ensure string dtype (avoids writing 'nan')
                                    try:
                                        prev_df["DUPLICATE_ACROSS_DIVISIONS"] = prev_df["DUPLICATE_ACROSS_DIVISIONS"].fillna("").astype(str)
                                    except Exception:
                                        prev_df["DUPLICATE_ACROSS_DIVISIONS"] = prev_df["DUPLICATE_ACROSS_DIVISIONS"].apply(lambda x: str(x) if not pd.isna(x) else "")
                                    prev_df.loc[prev_df["GAMEID"] == game_data.game_id, "DUPLICATE_ACROSS_DIVISIONS"] = "TRUE"
                                    # Always reorder columns so DUPLICATE_ACROSS_DIVISIONS is last
                                    cols_prev = list(prev_df.columns)
                                    if "DUPLICATE_ACROSS_DIVISIONS" in cols_prev:
                                        cols_prev = [c for c in cols_prev if c != "DUPLICATE_ACROSS_DIVISIONS"] + ["DUPLICATE_ACROSS_DIVISIONS"]
                                        prev_df = prev_df[cols_prev]
                                    prev_df.to_csv(path, index=False)
                                    self.logger.info(f"Marked duplicate {game_data.game_id} in previous file: {path}")
                                    # Also update file in Google Drive if upload is enabled
                                    if self.config.upload_to_gdrive and self.file_manager.file_exists_and_has_content(path):
                                        try:
                                            # Schedule upload after reconciliation completes
                                            self.logger.info(f"Scheduling upload for updated file: {path}")
                                            self.schedule_upload(path, year, month, gender, div)
                                        except Exception as e:
                                            self.logger.warning(f"Failed to schedule Google Drive upload for {path}: {e}")
                                except Exception as e:
                                    self.logger.warning(f"Unexpected error while updating previous CSV {path}: {e}")
                            # Register this game_id for this division
                            if game_data.game_id not in all_game_ids:
                                all_game_ids[game_data.game_id] = {}
                            all_game_ids[game_data.game_id][division] = csv_path
                    except Exception as e:
                        self.logger.error(f"Error scraping game {game_link}: {e}")
                        self.send_notification(
                            f"Error scraping game: {e}",
                            ErrorType.GAME_ERROR,
                            division=division,
                            date=f"{year}-{month}-{day}",
                            gender=gender,
                            game_link=game_link
                        )
                        continue
                # Schedule upload to Google Drive if enabled (uploads will run after reconciliation)
                if self.config.upload_to_gdrive and self.file_manager.file_exists_and_has_content(csv_path):
                    self.logger.info(f"Scheduling upload for completed CSV for {gender} {division}: {csv_path}")
                    self.schedule_upload(csv_path, year, month, gender, division)
                return scraped_games
            finally:
                if self.driver:
                    SeleniumUtils.safe_quit_driver(self.driver)
                    self.driver = None
        except Exception as e:
            error_msg = f"Error in scrape(): {e}"
            self.logger.error(error_msg)
            self.send_notification(
                error_msg,
                ErrorType.ERROR
            )
            return []
    
    def _load_scoreboard_page(self, url: str, division: str, gender: str, date: str) -> bool:
        """Load the scoreboard page and check for errors, with conditional retry."""
        max_retries = 3
        attempt = 0
        while attempt < max_retries:
            try:
                self.logger.info(f"Loading scoreboard page: {url} (attempt {attempt + 1}/{max_retries})")
                SeleniumUtils.human_like_delay(1.0, 2.0)
                self.driver.get(url)
                SeleniumUtils.human_like_delay(2.0, 4.0)
                wait = WebDriverWait(self.driver, self.config.wait_timeout)
                try:
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "gamePod-link")))
                    return True
                except TimeoutException:
                    error_msg = SeleniumUtils.check_for_errors(self.driver)
                    if error_msg:
                        self.logger.warning(f"{error_msg} for {url}")
                        self.send_notification(
                            f"{error_msg} for {url}",
                            ErrorType.WARNING,
                            division=division,
                            date=date,
                            gender=gender
                        )
                        if "rate limit" in error_msg.lower():
                            self.logger.warning("Rate limit exceeded, will NOT retry this link.")
                            return False
                        # Otherwise, retry after delay
                        attempt += 1
                        if attempt < max_retries:
                            self.logger.info("Retrying after 15 seconds...")
                            time.sleep(15)
                        continue
                    http_error = SeleniumUtils.check_http_status(self.driver)
                    if http_error:
                        self.logger.warning(f"{http_error} for {url}")
                        self.send_notification(
                            f"{http_error} for {url}",
                            ErrorType.ERROR,
                            division=division,
                            date=date,
                            gender=gender
                        )
                        attempt += 1
                        if attempt < max_retries:
                            self.logger.info("Retrying after 15 seconds...")
                            time.sleep(15)
                        continue
                    no_games_msg = f"No games found on scoreboard page: {url}"
                    self.logger.warning(no_games_msg)
                    self.send_notification(
                        no_games_msg,
                        ErrorType.INFO,
                        division=division,
                        date=date,
                        gender=gender
                    )
                    attempt += 1
                    if attempt < max_retries:
                        self.logger.info("Retrying after 15 seconds...")
                        time.sleep(15)
                    continue
            except WebDriverException as e:
                error_msg = f"Selenium WebDriver error loading scoreboard page {url}: {e}"
                self.logger.error(error_msg)
                self.send_notification(
                    error_msg,
                    ErrorType.ERROR,
                    division=division,
                    date=date,
                    gender=gender
                )
                attempt += 1
                if attempt < max_retries:
                    self.logger.info("Retrying after 15 seconds...")
                    time.sleep(15)
                continue
            except Exception as e:
                error_msg = f"Unexpected error loading scoreboard page {url}: {e}"
                self.logger.error(error_msg)
                self.send_notification(
                    error_msg,
                    ErrorType.ERROR,
                    division=division,
                    date=date,
                    gender=gender
                )
                attempt += 1
                if attempt < max_retries:
                    self.logger.info("Retrying after 15 seconds...")
                    time.sleep(15)
                continue
            break
        return False

    def reconcile_duplicates_for_date(self, year: str, month: str, day: str, gender: str) -> None:
        """
        Scan all division CSVs for the given date/gender, detect GAMEIDs present in more than
        one division, mark DUPLICATE_ACROSS_DIVISIONS=TRUE in all affected files, and update
        Google Drive copies if upload is enabled.

        This runs after a scraping session to ensure duplicates are consistently marked.
        """
        try:
            import pandas as pd
            from pathlib import Path

            base_dir = Path(self.file_manager.base_output_dir) / year / month / gender
            if not base_dir.exists():
                self.logger.info(f"No output for {year}-{month}-{day} {gender} to reconcile")
                return

            # Collect CSV files for divisions
            csv_paths = []
            for div_dir in base_dir.iterdir():
                if div_dir.is_dir():
                    csv_file = div_dir / f"basketball_{gender}_{div_dir.name}_{year}_{month}_{day}.csv"
                    if csv_file.exists():
                        csv_paths.append(csv_file)

            if not csv_paths:
                self.logger.info(f"No division CSVs found to reconcile for {year}-{month}-{day} {gender}")
                return

            # Read GAMEIDs from each file
            gid_to_paths = {}
            for p in csv_paths:
                try:
                    try:
                        df = pd.read_csv(p)
                    except Exception:
                        df = pd.read_csv(p, engine='python', sep=',', on_bad_lines='skip')
                    if 'GAMEID' in df.columns:
                        for gid in df['GAMEID'].astype(str).unique():
                            gid_to_paths.setdefault(gid, set()).add(p)
                except Exception as e:
                    self.logger.warning(f"Failed to read {p} during reconcile: {e}")
                    continue

            # Find duplicates
            duplicate_gids = {gid for gid, paths in gid_to_paths.items() if len(paths) > 1}
            if not duplicate_gids:
                self.logger.info(f"No cross-division duplicates found for {year}-{month}-{day} {gender}")
                return

            # Update each file marking duplicates
            for p in csv_paths:
                try:
                    try:
                        df = pd.read_csv(p)
                    except Exception:
                        df = pd.read_csv(p, engine='python', sep=',', on_bad_lines='skip')

                    if 'DUPLICATE_ACROSS_DIVISIONS' not in df.columns:
                        df['DUPLICATE_ACROSS_DIVISIONS'] = ''
                    # Ensure string dtype for the duplicate flag
                    try:
                        df['DUPLICATE_ACROSS_DIVISIONS'] = df['DUPLICATE_ACROSS_DIVISIONS'].fillna("").astype(str)
                    except Exception:
                        df['DUPLICATE_ACROSS_DIVISIONS'] = df['DUPLICATE_ACROSS_DIVISIONS'].apply(lambda x: str(x) if not pd.isna(x) else "")

                    mask = df['GAMEID'].astype(str).isin(duplicate_gids)
                    if mask.any():
                        df.loc[mask, 'DUPLICATE_ACROSS_DIVISIONS'] = 'TRUE'
                        # reorder column to put duplicate flag last
                        cols = [c for c in df.columns if c != 'DUPLICATE_ACROSS_DIVISIONS'] + ['DUPLICATE_ACROSS_DIVISIONS']
                        df = df[cols]
                        df.to_csv(p, index=False)
                        self.logger.info(f"Marked duplicates in {p}")
                        # update gdrive if enabled
                        if self.config.upload_to_gdrive:
                            # derive division from parent folder name and schedule upload
                            division = p.parent.name
                            try:
                                self.logger.info(f"Scheduling upload for reconciled file: {p}")
                                self.schedule_upload(str(p), year, month, gender, division)
                            except Exception as e:
                                self.logger.warning(f"Failed to schedule Google Drive upload for {p}: {e}")
                except Exception as e:
                    self.logger.warning(f"Failed to update file {p} during reconcile: {e}")
                    continue

            self.logger.info(f"Reconcile complete: marked {len(duplicate_gids)} duplicate GAMEIDs for {year}-{month}-{day} {gender}")
        except Exception as e:
            self.logger.error(f"Error during reconcile_duplicates_for_date: {e}")
            return
    
    def _extract_game_links(self) -> List[str]:
        """Extract game links from the scoreboard page."""
        try:
            box_scores = self.driver.find_elements(By.CLASS_NAME, "gamePod-link")
            game_links = [box_score.get_attribute('href') for box_score in box_scores if box_score.get_attribute('href')]
            return game_links
        except WebDriverException as e:
            error_msg = f"Selenium error finding game links: {e}"
            self.logger.error(error_msg)
            self.send_notification(
                error_msg,
                ErrorType.ERROR
            )
            return []
        except Exception as e:
            error_msg = f"Unexpected error finding game links: {e}"
            self.logger.error(error_msg)
            self.send_notification(
                error_msg,
                ErrorType.ERROR
            )
            return []
    
    def _scrape_single_game(
        self, 
        game_link: str, 
        year: str, 
        month: str, 
        day: str, 
        gender: str, 
        division: str,
        csv_path: str
    ) -> Optional[GameData]:
        """Scrape a single game's box score data."""
        game_id = extract_game_id_from_url(game_link)
        
        # Check if game already exists in CSV
        if self.is_duplicate(game_id, csv_path):
            self.logger.info(f"Game {game_id} already exists in {csv_path}, skipping...")
            return None
        
        # ...existing code...
        
        self.logger.info(f"Scraping: {game_link}")
        
        try:
            # Navigate to game page
            self.driver.get(game_link)
            self.logger.info(f"Successfully navigated to: {game_link}")
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, self.config.wait_timeout)
            
            # Check for team selector
            team_selector = SeleniumUtils.wait_for_element(
                self.driver, By.CLASS_NAME, "boxscore-team-selector", self.config.wait_timeout
            )
            if not team_selector:
                error_msg = f"Box score page may not exist or is not available for {game_link}"
                self.logger.warning(error_msg)
                self.send_notification(
                    error_msg,
                    ErrorType.WARNING,
                    division=division,
                    date=f"{year}-{month}-{day}",
                    gender=gender,
                    game_link=game_link
                )
                return None
            
            # Get team names
            team_names = self._extract_team_names(team_selector)
            if len(team_names) < 2:
                self.logger.warning(f"Not enough team names found for {game_link}")
                return None
            
            # Get team data
            team_one_data = self._extract_team_data(team_selector, team_names[0], team_names[1], game_id, game_link)
            if not team_one_data:
                return None
            
            # Switch to second team
            if not self._switch_to_second_team(team_selector, team_names[1]):
                return None
            
            # Get second team data
            team_two_data = self._extract_team_data(team_selector, team_names[1], team_names[0], game_id, game_link)
            if not team_two_data:
                return None
            
            # Create game data
            game_data = GameData(
                game_id=game_id,
                game_link=game_link,
                team_one=team_one_data,
                team_two=team_two_data,
                date=f"{year}-{month}-{day}",
                division=division,
                gender=gender
            )
            
            # Save to CSV
            if self.save_game_data(game_data, csv_path):
                self.logger.info(f"Successfully saved game data for {game_id}")
                return game_data
            else:
                self.logger.error(f"Failed to save game data for {game_id}")
                return None
                
        except Exception as e:
            error_msg = f"Error scraping game {game_link}: {e}"
            self.logger.error(error_msg)
            self.send_notification(
                error_msg,
                ErrorType.GAME_ERROR,
                division=division,
                date=f"{year}-{month}-{day}",
                gender=gender,
                game_link=game_link
            )
            return None
    
    def _extract_team_names(self, team_selector) -> List[str]:
        """Extract team names from the team selector."""
        try:
            child_divs = team_selector.find_elements(By.TAG_NAME, "div")
            team_names = [div.text.strip() for div in child_divs if div.text.strip()]
            return team_names
        except Exception as e:
            self.logger.error(f"Error extracting team names: {e}")
            return []
    
    def _extract_team_data(self, team_selector, team_name: str, opponent_name: str, game_id: str, game_link: str) -> Optional[TeamData]:
        """Extract data for a single team."""
        try:
            # Wait for box score table
            boxscore_table = SeleniumUtils.wait_for_element(
                self.driver, By.CLASS_NAME, 'gamecenter-tab-boxscore', self.config.wait_timeout
            )
            if not boxscore_table:
                self.logger.warning(f"Box score table not found")
                return None
            
            table = boxscore_table.find_element(By.TAG_NAME, 'table')
            df = pd.read_html(StringIO(table.get_attribute('outerHTML')))[0]
            
            if df.empty:
                self.logger.warning(f"Empty box score data for team {team_name}")
                return None
            
            # Remove last 2 rows (typically totals) from individual team data
            if len(df) > 2:
                df = df.iloc[:-2]
            
            return TeamData(
                team_name=team_name,
                opponent_name=opponent_name,
                game_id=game_id,
                game_link=game_link,
                stats=df
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting team data for {team_name}: {e}")
            return None
    
    def _switch_to_second_team(self, team_selector, second_team_name: str) -> bool:
        """Switch to the second team's data."""
        try:
            child_divs = team_selector.find_elements(By.TAG_NAME, "div")
            for div in child_divs:
                if div.text.strip() == second_team_name:
                    SeleniumUtils.safe_click(div)
                    time.sleep(self.config.sleep_time)  # Wait for the switch
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error switching to second team: {e}")
            return False
