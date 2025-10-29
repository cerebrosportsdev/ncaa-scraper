# Google Drive Setup Guide

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable Google Drive API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API" and click "Enable"

## Step 2: Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Choose "Desktop application"
4. Download the JSON file (you'll need the client_id and client_secret)

## Step 3: Set Up Environment Variables

Create a `.env` file in your project root with:

```env
# Google Drive Configuration
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=urn:ietf:wg:oauth:2.0:oob
GOOGLE_DRIVE_FOLDER_ID=your_base_folder_id_here  # Optional
GOOGLE_TOKEN_FILE=token.pickle

# Enable Google Drive upload
UPLOAD_TO_GDRIVE=true

# Other settings
OUTPUT_DIR=scraped_data
LOG_LEVEL=INFO
```

## Step 4: Run the Scraper with Google Drive Upload

```bash
# Build the Docker image
docker build -t ncaa-scraper .

# Run with Google Drive upload enabled
docker run --rm -v ${PWD}:/app/data ncaa-scraper --date 2025/02/06 --divisions d3 --genders women --upload-gdrive
```

## How It Works

1. **First Run**: The scraper will open a browser window for Google authentication
2. **Authentication**: You'll need to sign in and authorize the app
3. **Token Storage**: The access token is saved to `token.pickle` for future use
4. **Automatic Upload**: After scraping, CSV files are automatically uploaded to Google Drive
5. **Folder Structure**: Files are organized as `scraped_data/year/month/gender/division/`

## Folder Structure in Google Drive

```
scraped_data/
├── 2025/
│   └── 02/
│       └── women/
│           └── d3/
│               └── basketball_women_d3_2025_02_06.csv
```

## Troubleshooting

- **Authentication Issues**: Delete `token.pickle` and try again
- **Permission Errors**: Make sure the Google Drive API is enabled
- **Upload Failures**: Check that the credentials are correct in `.env`