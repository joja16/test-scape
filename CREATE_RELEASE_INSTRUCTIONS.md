# 📦 How to Create GitHub Release for Auto Scrape

Follow these steps to create a release and upload the executable to GitHub:

## Step 1: Navigate to GitHub Repository
1. Open your browser and go to: https://github.com/joja16/test-scape
2. Click on "Releases" on the right side of the page (or go to https://github.com/joja16/test-scape/releases)

## Step 2: Create New Release
1. Click **"Draft a new release"** button
2. Click **"Choose a tag"** and type: `v1.0.0`
3. Select **"Create new tag: v1.0.0 on publish"**
4. Set **Release title**: `Auto Scrape v1.0.0 - Initial Release`
5. Set **Target branch**: `main`

## Step 3: Add Release Description
Copy and paste the content from `RELEASE_NOTES.md` into the description field.

## Step 4: Upload the Executable
1. In the "Attach binaries" section, drag and drop or browse to select:
   - `D:\code\BOT\auto-scrape\dist\AutoScrape.exe` (395 MB)

2. Wait for the upload to complete (may take a few minutes due to file size)

## Step 5: Configure Release Settings
- ✅ Check **"Set as the latest release"**
- ⬜ Leave **"Set as a pre-release"** unchecked
- ⬜ Leave **"Create a discussion for this release"** as per preference

## Step 6: Publish
1. Click **"Publish release"** button
2. Your release will be live at: https://github.com/joja16/test-scape/releases/tag/v1.0.0

## Alternative: Using GitHub CLI (if installed)

If you have GitHub CLI installed, you can run this command instead:

```powershell
gh release create v1.0.0 `
  --title "Auto Scrape v1.0.0 - Initial Release" `
  --notes-file RELEASE_NOTES.md `
  dist\AutoScrape.exe
```

## Direct Links After Publishing
- Release Page: https://github.com/joja16/test-scape/releases/tag/v1.0.0
- Direct Download: https://github.com/joja16/test-scape/releases/download/v1.0.0/AutoScrape.exe

## File Location on Your Machine
The executable file to upload is located at:
```
D:\code\BOT\auto-scrape\dist\AutoScrape.exe
```

Size: ~395 MB

## Notes
- The file is large (395 MB) because it contains all dependencies
- Upload may take 2-5 minutes depending on your internet speed
- Users can download and run directly without Python installed
- The executable is not code-signed, so Windows may show security warnings

---

Once the release is created, the download link in the README.md will automatically work!
