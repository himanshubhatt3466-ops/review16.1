# Google Review Generator Pro (Windows 11)

A lightweight Windows desktop app with:
- Offline review-draft generator (English only)
- Natural / Professional / Friendly writing styles
- Short / Medium / Long drafts
- Copy and locally save drafts (SQLite)
- Google Business Profile review dashboard (OAuth; requires Google API access)
- Windows EXE build using GitHub Actions or `build_windows.bat`

## Important truthfulness and Google policy notes
This app generates **draft text only**. It does not create fake customer experiences, post reviews, or bulk-submit reviews. A person should edit the draft so it accurately reflects their genuine experience.

Google review access is not automatically available to every developer. Google requires Business Profile API access approval, a Google Cloud project, enabled APIs, and OAuth 2.0 credentials. The connected Google account must have access to the relevant verified Business Profile. See:
- https://developers.google.com/my-business/content/prereqs
- https://developers.google.com/my-business/content/basic-setup
- https://developers.google.com/my-business/content/review-data
- https://developers.google.com/my-business/content/implement-oauth

## Run the app from source
1. Install Python 3.11 or newer from https://www.python.org/downloads/ (enable **Add Python to PATH**).
2. Extract this ZIP.
3. Open the extracted folder.
4. Double-click `build_windows.bat` to install dependencies and build the EXE.
5. Run `dist\GoogleReviewGeneratorPro.exe`.

The draft generator works without Google credentials or internet access. Google review loading requires internet access.

## Build EXE using GitHub (no Python installation on your PC)
1. Sign in at https://github.com and create a new repository, e.g. `GoogleReviewGeneratorPro`.
2. Upload the extracted project files and folders (including `.github/workflows/build-windows.yml`) to the repository.
3. Open the repository's **Actions** tab.
4. Select **Build Windows EXE**. If it is not already running, click **Run workflow**.
5. Wait for the green successful run.
6. Open that workflow run and download the artifact named `GoogleReviewGeneratorPro-Windows`.
7. Extract the downloaded artifact ZIP and run `GoogleReviewGeneratorPro.exe`.

## Connect Google Business Profile
### A. Request API access
1. Use the Google account that owns/manages the Business Profile.
2. Create a project in Google Cloud Console: https://console.cloud.google.com/
3. Request Business Profile API basic access as described in Google's prerequisites guide.
4. Wait for Google's approval. A zero quota means access has not been granted yet.
5. Enable the Business Profile APIs required by the official setup guide.

### B. Create OAuth credentials
1. In Google Cloud Console, configure the OAuth consent screen.
2. Create an OAuth Client ID with application type **Desktop app**.
3. Download the client JSON file.
4. In this app, open **Settings → Choose credentials.json** and select that downloaded JSON.
5. Click **Connect Google account** and authorize the Google account that manages the business.
6. Click **Load locations** in Settings. If account names appear, click **Load locations** again to load the locations for the selected account.
7. Select a location and open **Google Reviews → Refresh reviews**.

The app stores its token and local draft database under:
`%APPDATA%\GoogleReviewGeneratorPro\`

To disconnect, close the app and delete `token.json` from that folder. You can revoke app access from your Google Account security settings.

## Troubleshooting
- **No accounts/locations:** Ensure the signed-in Google account is an owner/manager of a verified Business Profile and that API access was approved.
- **API access / 403 error:** Check API approval, enabled APIs, OAuth consent configuration, and quota in Google Cloud Console.
- **OAuth JSON error:** Download an OAuth Client ID JSON for **Desktop app**, not an API key or service-account key.
- **No reviews displayed:** Confirm the selected location is verified and has reviews; check the Google API response/error message.
- **Windows SmartScreen:** Windows may show a warning for an unsigned EXE. Only run a build you created from this source.

## Project structure
- `app.py` — desktop application
- `requirements.txt` — Python dependencies
- `build_windows.bat` — local Windows EXE build
- `.github/workflows/build-windows.yml` — automatic Windows EXE build
