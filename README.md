# Patreon Chapter Downloader Bot

A Discord bot that fetches chapters from Patreon posts and compiles them into an EPUB file. The bot provides an interactive dropdown menu for selecting chapters and generates an EPUB with chapters ordered from oldest to newest. It uses `undetected_chromedriver` for stealthy web scraping and maintains a persistent browser session for efficiency.

## Features
- **Interactive Chapter Selection**: Select posts via a Discord dropdown menu (up to 20 chapters).
- **EPUB Generation**: Downloads selected posts and compiles them into a single EPUB file in a separate thread to avoid blocking the bot.
- **Persistent Browser**: Uses a single Chrome browser instance with a 5-minute inactivity timeout to reduce overhead.
- **Dynamic Filenames**: EPUB filenames are generated based on the first and last chapter titles with a character limit.

## Prerequisites
- **Python 3.8+**
- **Google Chrome Browser** (for `undetected_chromedriver`)
- **Patreon Account Cookies** (for authentication)
- **Discord Bot Token**

## Installation

### 1. Install Dependencies
Install the required Python packages using pip:
```bash
pip install discord.py undetected-chromedriver beautifulsoup4 ebooklib
```

### 2. Prepare Chrome
Ensure Google Chrome is installed in a default location (e.g., `C:\Program Files\Google\Chrome\Application\chrome.exe` on Windows, `/usr/bin/google-chrome` on Linux). `undetected_chromedriver` automatically downloads and patches ChromeDriver.

### 3. Prepare Patreon Cookies
The bot requires a `cookies.json` file with authenticated cookies to access Patreon content:
1. Log into Patreon using Chrome.
2. Use a browser extension (e.g., "EditThisCookie") to export your cookies as a JSON file.
3. Save the file as `cookies.json` in the project directory.

- **Note**: Ensure cookies include a valid `session_id` and grant access to desired content. Cookies may expire (e.g., `__cf_bm` expires March 3, 2026, at 07:24:05 UTC), requiring updates.
- **Alternatively**: Use the script `get-cookies.py` with your Patreon login details to generate `cookies.json`.

### 4. Set Up Discord Bot Token
1. Create a bot in the [Discord Developer Portal](https://discord.com/developers/applications).
2. Under the "Bot" tab, enable the "Message Content Intent".
3. Copy the bot token.
4. Replace `'YOUR_BOT_TOKEN_HERE'` in `bot.py` with your token.

### 5. Run the Bot
```bash
python bot.py
```

## Usage

### Invite the Bot to Your Server
1. In the Discord Developer Portal, go to the "OAuth2" tab.
2. Use the "URL Generator" to create an invite link with the following scopes and permissions:
   - Scopes: `bot`
   - Permissions: `Send Messages`, `Attach Files`
3. Invite the bot to your server using the generated link.

### Commands
- **`?fetch <patreon_url>`**
  - Fetches up to 20 chapters from the specified Patreon URL.
  - Displays a dropdown menu to select chapters.
  - After selection, click the "Download" button to receive an EPUB file.
  - Example: `?fetch https://www.patreon.com/c/{creator}/posts`

### EPUB Details
- Chapters are ordered in the EPUB from oldest to newest.
- The EPUB filename is generated based on the first and last chapter titles (e.g., `OldestTitle-NewestTitle.epub`).
- Each chapter includes a heading (`<h1>`) and content (`<p>`).

## Project Structure
- `bot.py`: Main script containing the bot logic.
- `cookies.json`: File containing Patreon authentication cookies (not included in the repository).

## Dependencies
- `discord.py`: For Discord bot functionality.
- `undetected_chromedriver`: For stealthy web scraping of Patreon content.
- `beautifulsoup4`: For parsing HTML content.
- `ebooklib`: For generating EPUB files.

## Troubleshooting
- **Browser Not Opening**: Ensure Chrome is installed in a default location. Check logs for ChromeDriver errors.
- **Invalid Cookies**: If chapters fail to load, verify `cookies.json` contains valid Patreon cookies. Update by re-exporting from Chrome.
- **Network Issues**: The bot retries failed requests three times with a 2-second delay. Check logs (`INFO`, `WARNING`, `ERROR`) for details.
- **File Size Limits**: Discord has an 8MB file upload limit (25MB/100MB for boosted servers). Large EPUBs may fail to upload.
- **Heartbeat Blocked**: Threading ensures Selenium doesn’t block the Discord event loop; verify no delays in logs.

## Logging
The bot logs activity to the console:
- `INFO`: General operations (e.g., browser opening, cookies loaded).
- `WARNING`: Non-critical issues (e.g., failed content fetch attempt).
- `ERROR`: Critical failures (e.g., unable to create EPUB).

## Notes
- **Browser Management**: Uses a single Chrome instance that closes after 5 minutes of inactivity to conserve resources. Runs EPUB creation in a separate thread.
- **Chapter Limit**: Capped at 20 chapters per fetch to fit Discord's dropdown menu limits.
- **Stealth**: `undetected_chromedriver` bypasses many bot detection methods; avoid headless mode if Patreon blocks it.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request with your changes.
