# Google Drive Integration Setup

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Get Google Drive API Credentials

1. **Go to Google Cloud Console:**
   - Visit [https://console.cloud.google.com/](https://console.cloud.google.com/)

2. **Create a new project or select existing:**
   - Click "Select a project" → "New Project"
   - Name it "NCAA Scraper" or similar

3. **Enable Google Drive API:**
   - Go to "APIs & Services" → "Library"
   - Search for "Google Drive API"
   - Click on it and press "Enable"

4. **Create credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Name it "NCAA Scraper Desktop"
   - Click "Create"

5. **Download credentials:**
   - Click the download button (⬇️) next to your new credential
   - Save the file as `credentials.json` in your project folder
   - **Note:** You'll need to extract the client_id and client_secret from this file for the .env configuration

## Step 3: Configure Environment Variables

1. **Copy the configuration template:**
   ```bash
   cp config.env .env
   ```

2. **Extract credentials from credentials.json:**
   - Open `credentials.json` in a text editor
   - Find the `client_id` and `client_secret` values
   - Copy these values to your `.env` file

3. **Edit your .env file:**
   ```bash
   # Replace these with your actual values from credentials.json
   GOOGLE_CLIENT_ID=your_actual_client_id_here
   GOOGLE_CLIENT_SECRET=your_actual_client_secret_here
   GOOGLE_REDIRECT_URI=urn:ietf:wg:oauth:2.0:oob
   
   # Optional: Set a default Google Drive folder ID
   # GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
   ```

## Step 4: First Run (Authentication)

Run the scraper with upload enabled:

```bash
python ncaa_scraper.py --upload-gdrive --date 2025/10/21
```

**On first run:**
1. A browser window will open
2. Sign in to your Google account
3. Grant permissions to the app
4. You'll see "Authentication successful" message
5. A `token.pickle` file will be created (keep this file!)

## Step 5: Usage Examples

### Basic scraping with upload:
```bash
python ncaa_scraper.py --upload-gdrive
```

### Scrape specific date and upload:
```bash
python ncaa_scraper.py --date 2025/10/21 --upload-gdrive
```

### Upload to specific Google Drive folder:
```bash
python ncaa_scraper.py --upload-gdrive --gdrive-folder-id "1ABC123DEF456"
```

### Backfill with upload:
```bash
python ncaa_scraper.py --backfill --upload-gdrive
```

## Step 6: Find Your Google Drive Folder ID (Optional)

If you want to upload to a specific folder:

1. **Open Google Drive in browser**
2. **Navigate to your desired folder**
3. **Look at the URL:**
   - URL: `https://drive.google.com/drive/folders/1ABC123DEF456GHI789`
   - Folder ID: `1ABC123DEF456GHI789`

## File Structure

Your files will be organized in Google Drive as:
```
NCAA_Data/
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
│   └── 10/
│       └── men/
│           └── d1/
│               └── basketball_men_d1_2025_10_21.csv
```

## Troubleshooting

### "Google Drive credentials not found in environment variables"
- Make sure you created a `.env` file from `config.env`
- Verify that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in your `.env` file
- Check that the values match those from your `credentials.json` file

### "credentials.json not found" (Legacy)
- This error should no longer appear with the new environment variable setup
- If you see this, make sure you're using the updated version of the scraper

### "Authentication failed"
- Delete `token.pickle` and try again
- Make sure you granted all required permissions
- Verify your environment variables are correct

### "Permission denied"
- Check that the Google Drive API is enabled
- Verify your credentials are correct in the `.env` file

### Files not uploading
- Check your internet connection
- Verify the folder ID is correct (if using one)
- Check the logs for specific error messages
- Ensure your `.env` file is in the same directory as the script

## Security Notes

- **Keep your `.env` file secure** - it contains your Google OAuth2 credentials
- **Don't commit `.env` or `credentials.json` to version control**
- **The `token.pickle` file contains your access token**
- **If compromised, revoke access in Google Cloud Console**
- **The new environment variable approach is more secure than storing credentials in JSON files**

## Automation

You can now run this as a scheduled task that automatically uploads to Google Drive:

### Windows Task Scheduler:
1. Create a new task
2. Set trigger (daily, weekly, etc.)
3. Action: Run `python ncaa_scraper.py --upload-gdrive`

### Linux/Mac Cron:
```bash
# Run daily at 6 AM
0 6 * * * cd /path/to/your/project && python ncaa_scraper.py --upload-gdrive
```
