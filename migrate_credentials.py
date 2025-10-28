#!/usr/bin/env python3
"""
Simple .env setup helper
"""

import os

def create_env_file():
    """Create .env file with Google Drive credentials"""
    
    print("🔧 Setting up .env file for Google Drive integration")
    print("=" * 50)
    
    # Check if .env already exists
    if os.path.exists(".env"):
        response = input("⚠️  .env already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return False
    
    print("\n📝 Please enter your Google OAuth2 credentials:")
    print("(Get these from Google Cloud Console - see GOOGLE_DRIVE_SETUP.md)")
    print()
    
    client_id = input("GOOGLE_CLIENT_ID: ").strip()
    client_secret = input("GOOGLE_CLIENT_SECRET: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Both CLIENT_ID and CLIENT_SECRET are required!")
        return False
    
    # Optional folder ID
    folder_id = input("GOOGLE_DRIVE_FOLDER_ID (optional, press Enter to skip): ").strip()
    
    # Optional Discord webhook
    discord_webhook = input("DISCORD_WEBHOOK_URL (optional, press Enter to skip): ").strip()
    
    # Create .env content
    env_content = f"""# Google Drive API Configuration
GOOGLE_CLIENT_ID={client_id}
GOOGLE_CLIENT_SECRET={client_secret}
GOOGLE_REDIRECT_URI=urn:ietf:wg:oauth:2.0:oob
"""
    
    if folder_id:
        env_content += f"GOOGLE_DRIVE_FOLDER_ID={folder_id}\n"
    else:
        env_content += "# GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here\n"
    
    if discord_webhook:
        env_content += f"DISCORD_WEBHOOK_URL={discord_webhook}\n"
    else:
        env_content += "# DISCORD_WEBHOOK_URL=your_discord_webhook_url_here\n"
    
    env_content += "\n# Optional: Custom token file path\n# GOOGLE_TOKEN_FILE=token.pickle\n"
    
    # Write .env file
    with open(".env", "w") as f:
        f.write(env_content)
    
    print(f"\n✅ Successfully created .env file!")
    print("📝 Next step: Run the scraper with --upload-gdrive flag")
    
    return True

if __name__ == "__main__":
    create_env_file()
