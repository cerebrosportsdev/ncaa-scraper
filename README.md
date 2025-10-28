# NCAA Basketball Box Score Scraper

An automated scraper for NCAA basketball box scores with Google Drive integration.

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/ncaa-basketball-scraper.git
cd ncaa-basketball-scraper
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Set Up Google Drive (Optional)
Follow the instructions in `GOOGLE_DRIVE_SETUP.md` to enable automatic uploads.

### 4. Run the Scraper
```bash
# Scrape yesterday's games
python ncaa_scraper.py

# Scrape specific date
python ncaa_scraper.py --date 2025/01/15

# Upload to Google Drive
python ncaa_scraper.py --upload-gdrive
```

## 📁 Features

- 🏀 Scrapes NCAA basketball box scores (Men's & Women's, D1/D2/D3)
- 📁 Organized folder structure by year/month/gender/division
- ☁️ Automatic Google Drive upload with organized folders
- 🔄 Duplicate prevention (session and file-based)
- 📊 Batch processing and smart skipping
- 🗓️ Date-based scraping with backfill support

## 📊 Usage

```bash
python ncaa_scraper.py [OPTIONS]

Options:
  --date DATE              Date in YYYY/MM/DD format (default: yesterday)
  --output-dir DIR         Output directory for CSV files (default: scraped_data)
  --backfill              Run backfill for specific dates
  --upload-gdrive         Upload scraped data to Google Drive
  --gdrive-folder-id ID   Google Drive folder ID to upload to
```

## 📂 File Structure

```
scraped_data/
├── 2025/
│   ├── 01/
│   │   ├── men/
│   │   │   ├── d1/
│   │   │   │   └── basketball_men_d1_2025_01_15.csv
│   │   │   ├── d2/
│   │   │   └── d3/
│   │   └── women/
│   │       ├── d1/
│   │       ├── d2/
│   │       └── d3/
```

## 🔧 Requirements

- Python 3.7+
- Chrome browser
- Google Drive API credentials (optional)

## 📋 Setup Files

- `requirements.txt` - Python dependencies
- `GOOGLE_DRIVE_SETUP.md` - Google Drive API setup guide
- `ncaa_scraper.py` - Main scraper script
- `run_scraper.py` - Simple runner script

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 Notes

- The scraper automatically skips days that already have data
- Google Drive integration is optional but recommended for data backup
- All sensitive files (credentials, tokens) are gitignored for security

## 🐛 Troubleshooting

See `GOOGLE_DRIVE_SETUP.md` for common issues and solutions.

## 📄 License

MIT License