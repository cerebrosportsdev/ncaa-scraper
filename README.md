# NCAA Basketball Box Score Scraper

A modular, well-structured scraper for NCAA basketball box scores with Google Drive integration.

## 🚀 Quick Start

### 1. Set Up Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Set up Google Drive credentials (optional)
python migrate_credentials.py
```

### 2. Run the Scraper
```bash
# Scrape yesterday's games
python main.py

# Scrape specific date
python main.py --date 2025/01/15

# Upload to Google Drive
python main.py --upload-gdrive

# Scrape multiple divisions and genders
python main.py --divisions d1 d2 d3 --genders men women
```

## 📁 New Architecture

The refactored scraper is organized into focused, modular components:

```
ncaa_scraper/
├── config/              # Configuration management
│   ├── settings.py      # Main configuration class
│   └── constants.py     # Constants and enums
├── models/              # Data models
│   ├── game_data.py     # Game and team data models
│   └── scraping_config.py # Scraping configuration models
├── utils/               # Utility functions
│   ├── date_utils.py    # Date handling
│   ├── url_utils.py     # URL generation and parsing
│   └── validators.py    # Input validation
├── storage/             # Storage operations
│   ├── file_manager.py  # Local file operations
│   ├── csv_handler.py   # CSV-specific operations
│   └── google_drive.py  # Google Drive integration
├── notifications/       # Notification systems
│   ├── base_notifier.py # Base notification interface
│   └── discord_notifier.py # Discord notifications
├── scrapers/            # Scraping logic
│   ├── base_scraper.py  # Base scraper class
│   ├── ncaa_scraper.py  # NCAA-specific scraper
│   └── selenium_utils.py # Selenium utilities
└── main.py              # Main entry point
```

## ✨ Key Improvements

### 1. **Modular Design**
- Each component has a single responsibility
- Easy to test, maintain, and extend
- Clear separation of concerns

### 2. **Better Error Handling**
- Centralized error handling strategies
- Comprehensive logging throughout
- Graceful degradation on failures

### 3. **Type Safety**
- Type hints throughout the codebase
- Data models with validation
- Better IDE support and debugging

### 4. **Configuration Management**
- Centralized configuration with validation
- Environment variable support
- Easy to override settings

### 5. **Extensibility**
- Base classes for easy extension
- Plugin-like architecture for notifications
- Easy to add new scrapers or storage backends

## 🔧 Usage

### Basic Usage
```bash
# Scrape yesterday's women's D3 games
python main.py

# Scrape specific date
python main.py --date 2025/01/15

# Upload to Google Drive
python main.py --upload-gdrive
```

### Advanced Usage
```bash
# Scrape multiple divisions
python main.py --divisions d1 d2 d3

# Scrape both genders
python main.py --genders men women

# Custom output directory
python main.py --output-dir /path/to/data

# Backfill specific dates
python main.py --backfill
```

### Programmatic Usage
```python
from ncaa_scraper.config import get_config
from ncaa_scraper.scrapers import NCAAScraper
from ncaa_scraper.utils import generate_ncaa_urls
from datetime import date

# Get configuration
config = get_config()

# Create scraper
scraper = NCAAScraper(config)

# Generate URLs
urls = generate_ncaa_urls("2025/01/15")

# Scrape data
for url in urls:
    games = scraper.scrape(url)
    print(f"Scraped {len(games)} games from {url}")
```

## 📊 Features

- 🏀 Scrapes NCAA basketball box scores (Men's & Women's, D1/D2/D3)
- 📁 Organized folder structure by year/month/gender/division
- ☁️ Automatic Google Drive upload with organized folders
- 🔄 Duplicate prevention (session and file-based)
- 📊 Batch processing and smart skipping
- 🗓️ Date-based scraping with backfill support
- 🔔 Discord notifications for errors and warnings
- 🧪 Comprehensive error handling and logging
- 🔧 Modular, extensible architecture

## 🛠️ Development

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=ncaa_scraper tests/
```

### Adding New Features
1. **New Scraper**: Extend `BaseScraper` class
2. **New Storage**: Implement storage interface
3. **New Notifications**: Extend `BaseNotifier` class
4. **New Utilities**: Add to appropriate utility module

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings for all public methods
- Write tests for new functionality

## 🔄 Migration from Old Version

The refactored version is backward compatible with the original:

1. **Same CLI interface**: All original command-line arguments work
2. **Same output format**: CSV files have the same structure
3. **Same configuration**: Uses the same `.env` file format
4. **Same features**: All original functionality is preserved

### Key Differences
- **Better organization**: Code is split into logical modules
- **Improved error handling**: More robust error recovery
- **Type safety**: Better IDE support and fewer runtime errors
- **Extensibility**: Easy to add new features
- **Testability**: Each component can be tested independently

## 📝 Configuration

### Environment Variables
```bash
# OAuth client
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8080/

# OAuth token (base64 of token.pickle)
GOOGLE_TOKEN_FILE_B64=your_base64_token_pickle

# Optional notifications
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here

# Optional runtime
OUTPUT_DIR=scraped_data
LOG_LEVEL=INFO
```

### Configuration File
You can also create a `config.yaml` file for more complex configurations:

```yaml
scraper:
  output_dir: "scraped_data"
  wait_timeout: 15
  sleep_time: 2

google_drive:
  enabled: true
  folder_id: "your_folder_id"

notifications:
  discord:
    enabled: true
    webhook_url: "your_webhook_url"
```

## 🐛 Troubleshooting

### Common Issues
1. **Import Errors**: Make sure you're in the project root directory
2. **Selenium Issues**: Ensure Chrome browser is installed
3. **Google Drive Auth**: Run `python migrate_credentials.py` to set up credentials
4. **Permission Errors**: Check file/directory permissions

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=DEBUG python main.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License

---

## 🚀 Default Behavior: All Divisions, All Genders, Yesterday's Games

```bash
docker run --rm ncaa-scraper
```

That's it — the scraper will automatically:

- Check Google Drive for existing files
- Scrape all divisions (D1, D2, D3)
- Scrape both genders (Men, Women)
- Use yesterday's date automatically
- Upload to Google Drive with duplicate detection

### What Gets Scraped

| Division | Gender | Example Date |
|----------|--------|--------------|
| D1 | Men | 2025-02-14 |
| D1 | Women | 2025-02-14 |
| D2 | Men | 2025-02-14 |
| D2 | Women | 2025-02-14 |
| D3 | Men | 2025-02-14 |
| D3 | Women | 2025-02-14 |

### Example Output

```
2025-10-29 04:30:12,011 - INFO - Pre-checking Google Drive for existing files...
2025-10-29 04:30:12,015 - INFO - ✓ men d1 2025-02-14 already exists in Google Drive
2025-10-29 04:30:12,016 - INFO - ✗ women d1 2025-02-14 needs scraping
2025-10-29 04:30:12,017 - INFO - ✓ men d2 2025-02-14 already exists in Google Drive
2025-10-29 04:30:12,018 - INFO - ✗ women d2 2025-02-14 needs scraping
2025-10-29 04:30:12,019 - INFO - ✓ men d3 2025-02-14 already exists in Google Drive
2025-10-29 04:30:12,020 - INFO - ✗ women d3 2025-02-14 needs scraping
2025-10-29 04:30:12,021 - INFO - Google Drive pre-check complete: 3/6 files already exist
```

### Customization Options

```bash
# Specific date
docker run --rm ncaa-scraper --date 2025/02/15

# Specific division
docker run --rm ncaa-scraper --divisions d3

# Specific gender
docker run --rm ncaa-scraper --genders women

# Disable Google Drive
docker run --rm ncaa-scraper --no-upload-gdrive
```

---

## Google Drive Upload is Now Default

Google Drive upload is enabled by default for all scraping operations:

- No need to add `--upload-gdrive`
- Automatic duplicate detection before scraping
- Pre-checking of Google Drive before starting
- Intelligent uploads (only new/updated files)

### Commands

```bash
# Default behavior (uploads enabled)
docker run --rm ncaa-scraper --date 2025/02/06 --divisions d3 --genders women

# Disable Google Drive if needed
docker run --rm ncaa-scraper --date 2025/02/06 --divisions d3 --genders women --no-upload-gdrive

# Explicit enable still works
docker run --rm ncaa-scraper --date 2025/02/06 --divisions d3 --genders women --upload-gdrive
```

### Environment Variables

```env
UPLOAD_TO_GDRIVE=true   # default
# UPLOAD_TO_GDRIVE=false to disable
```

---

## Google Drive Duplicate Detection

The scraper prevents unnecessary uploads by:

1. Checking for existing files in the target folder
2. Comparing local vs Google Drive modification timestamps (UTC)
3. Smartly deciding to upload, update, or skip

### Benefits

- Faster runs and reduced API calls
- No duplicates; always keeps most recent versions
- Detailed logging and upload stats

### Example Log Output

```
2025-10-29 04:30:12,015 - INFO - Google Drive file ... is up to date, skipping upload
```

```env
# Required env for GDrive
UPLOAD_TO_GDRIVE=true
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_DRIVE_FOLDER_ID=your_base_folder_id
```

---

## Google Drive Setup Guide

1. Create a Google Cloud project and enable Google Drive API
2. Create OAuth credentials (Desktop application)
3. Set environment variables in `.env`
4. Run the scraper; token saved to `token.pickle`

```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=urn:ietf:wg:oauth:2.0:oob
GOOGLE_DRIVE_FOLDER_ID=your_base_folder_id_here
GOOGLE_TOKEN_FILE=token.pickle
UPLOAD_TO_GDRIVE=true
OUTPUT_DIR=scraped_data
LOG_LEVEL=INFO
```

---

## Selenium WebDriver Fixes

Key fixes for Chrome/ChromeDriver reliability:

- WebDriverManager for automatic driver versioning
- Retry mechanism on driver creation with cleanup
- Improved headless and Docker stability flags
- Safe driver quit and resource cleanup

Local:

```bash
pip install -r requirements.txt
python main.py
```

Docker:

```bash
docker build -t ncaa-scraper .
docker run ncaa-scraper
```

---

## GitHub Actions Setup Guide

### Pick one workflow
- `/.github/workflows/ncaa-scraper.yml` (regular): faster startup on GitHub runners.
- `/.github/workflows/ncaa-scraper-docker.yml` (docker): highest reproducibility.

Both are scheduled to run daily at 06:00 UTC. If you keep both, both will run; disable `schedule` in one if you only want a single daily run.

### Authentication for Google Drive

1) OAuth token (recommended for personal My Drive)
- Secrets to add:
  - `GOOGLE_TOKEN_FILE_B64` – base64 of your local `token.pickle`
  - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
  - `GOOGLE_DRIVE_FOLDER_ID` (optional but recommended)
  - `DISCORD_WEBHOOK_URL` (optional)
- Create `token.pickle` locally by running `python main.py` once and completing the browser login.
- Base64 (PowerShell):
  ```powershell
  $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes(".\token.pickle"))
  $b64 | Set-Clipboard
  ```
  Paste clipboard into the `GOOGLE_TOKEN_FILE_B64` secret.

2) Service Account (optional; requires Shared Drive)
- Use `GOOGLE_CREDENTIALS_JSON_B64` and a Shared Drive folder shared with the service account.
- Service accounts cannot upload to personal My Drive.

### Features
- Daily schedule at 6:00 AM UTC
- Manual triggers with inputs (date/divisions/genders/backfill)
- Artifacts for data and logs; automatic cleanup

### Change schedule
In the chosen workflow file:
```yaml
schedule:
  - cron: '0 6 * * *'
```

### Workflows
- Regular: `/.github/workflows/ncaa-scraper.yml`
- Docker: `/.github/workflows/ncaa-scraper-docker.yml`