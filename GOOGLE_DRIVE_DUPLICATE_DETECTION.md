# Google Drive Duplicate Detection

## 🚀 **New Features Added**

The NCAA scraper now includes intelligent duplicate detection for Google Drive uploads, preventing unnecessary uploads and saving time and bandwidth.

## **How It Works**

### **1. File Existence Check**
- Checks if a file with the same name already exists in the target Google Drive folder
- Searches by exact filename match within the specified folder

### **2. Timestamp Comparison**
- Compares local file modification time with Google Drive file modification time
- Only uploads if the local file is newer than the Google Drive version
- Handles timezone differences properly using UTC

### **3. Smart Upload Logic**
- **New file**: Uploads immediately
- **Existing file, local newer**: Updates the existing file
- **Existing file, Google Drive newer**: Skips upload (file is up-to-date)
- **Existing file, same timestamp**: Skips upload (no changes)

## **Benefits**

### **⚡ Performance**
- **Faster runs**: Skips unnecessary uploads
- **Bandwidth savings**: Only uploads when needed
- **API quota preservation**: Reduces Google Drive API calls

### **🔄 Reliability**
- **No duplicates**: Prevents multiple copies of the same file
- **Data integrity**: Always keeps the most recent version
- **Error handling**: Graceful fallback if timestamp comparison fails

### **📊 Visibility**
- **Detailed logging**: Shows why files are skipped or uploaded
- **Upload statistics**: Reports folder stats after upload
- **Progress tracking**: Clear indication of what's happening

## **Example Log Output**

```
2025-10-29 04:30:12,011 - INFO - Preparing to upload scraped_data/2025/02/women/d3/basketball_women_d3_2025_02_06.csv to Google Drive...
2025-10-29 04:30:12,015 - INFO - File already exists in Google Drive: basketball_women_d3_2025_02_06.csv (ID: 1ABC123, Modified: 2025-10-29T04:30:10.000Z, Size: 15432)
2025-10-29 04:30:12,016 - INFO - Google Drive file basketball_women_d3_2025_02_06.csv is up to date, skipping upload
2025-10-29 04:30:12,017 - INFO - File already exists and is up-to-date in Google Drive, skipping upload
```

Or for a new/updated file:

```
2025-10-29 04:30:12,011 - INFO - Preparing to upload scraped_data/2025/02/women/d3/basketball_women_d3_2025_02_06.csv to Google Drive...
2025-10-29 04:30:12,015 - INFO - File already exists in Google Drive: basketball_women_d3_2025_02_06.csv (ID: 1ABC123, Modified: 2025-10-29T04:25:10.000Z, Size: 15432)
2025-10-29 04:30:12,016 - INFO - Local file basketball_women_d3_2025_02_06.csv is newer than Google Drive version, will update
2025-10-29 04:30:12,017 - INFO - Successfully updated scraped_data/2025/02/women/d3/basketball_women_d3_2025_02_06.csv in Google Drive. File ID: 1ABC123
2025-10-29 04:30:12,018 - INFO - Google Drive folder stats: 15 files, 8 CSV files, 2.34 MB total
```

## **Configuration Options**

### **Environment Variables**
```env
# Enable Google Drive upload with duplicate detection
UPLOAD_TO_GDRIVE=true

# Google Drive credentials
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_DRIVE_FOLDER_ID=your_base_folder_id
```

### **Command Line**
```bash
# Upload with duplicate detection (default behavior)
docker run --rm ncaa-scraper --date 2025/02/06 --divisions d3 --genders women --upload-gdrive

# Force overwrite all files (bypasses duplicate detection)
# This would require modifying the code to pass overwrite=True
```

## **Technical Details**

### **Methods Added**
- `file_exists()`: Check if file exists in Google Drive
- `should_upload_file()`: Intelligent decision on whether to upload
- `get_upload_stats()`: Get folder statistics
- Enhanced `upload_file()`: Uses duplicate detection by default

### **Dependencies Added**
- `pytz>=2023.3`: For timezone handling

### **Error Handling**
- Graceful fallback if timestamp comparison fails
- Continues upload if file existence check fails
- Detailed error logging for troubleshooting

## **GitHub Actions Integration**

The duplicate detection works seamlessly with GitHub Actions:

```yaml
- name: Run NCAA Scraper with Google Drive
  run: |
    python main.py --date $(date +%Y/%m/%d) --divisions d3 --genders women --upload-gdrive
```

The scraper will:
1. Check if files already exist in Google Drive
2. Only upload new or updated files
3. Skip files that are already up-to-date
4. Provide detailed logging for monitoring

## **Monitoring and Debugging**

### **Log Levels**
- `INFO`: Normal operation (file checks, upload decisions)
- `WARNING`: Non-critical issues (timestamp comparison failures)
- `ERROR`: Critical failures (authentication, upload errors)

### **Statistics**
After each upload, the scraper reports:
- Total files in folder
- Number of CSV files
- Total folder size
- File type breakdown

This intelligent duplicate detection makes the scraper much more efficient for automated workflows, especially in GitHub Actions where you want to avoid unnecessary uploads and API calls.
