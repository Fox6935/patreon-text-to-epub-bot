import discord
from discord.ext import commands
from discord.ui import Select, View, Button
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
import os
import logging
import time
import threading
import re
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

# Create the bot instance
bot = commands.Bot(command_prefix='?', intents=intents)

# Define SafeChrome
class SafeChrome(uc.Chrome):
    def __del__(self):
        pass

# Global browser management
class BrowserManager:
    def __init__(self):
        self.browser = None
        self.timer = None
        self.lock = threading.Lock()
        self.inactivity_timeout = 300  # 5 minutes

    def get_browser(self):
        with self.lock:
            if self.browser is None:
                logging.info("Opening new browser instance")
                options = uc.ChromeOptions()
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                self.browser = SafeChrome(options=options)
                self.browser.get('https://www.patreon.com/')
                try:
                    with open('cookies.json', 'r') as file:
                        cookies = json.load(file)
                    for cookie in cookies:
                        self.browser.add_cookie(cookie)
                    logging.info("Cookies loaded successfully")
                except Exception as e:
                    logging.error(f"Failed to load cookies: {e}")
            self._reset_timer()
            return self.browser

    def _reset_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.inactivity_timeout, self._close_browser)
        self.timer.start()

    def _close_browser(self):
        with self.lock:
            if self.browser:
                logging.info("Closing browser due to inactivity")
                self.browser.quit()
                self.browser = None
            self.timer = None

    def shutdown(self):
        with self.lock:
            if self.browser:
                logging.info("Shutting down browser")
                self.browser.quit()
                self.browser = None
            if self.timer:
                self.timer.cancel()
                self.timer = None

# Instantiate browser manager
browser_manager = BrowserManager()
executor = ThreadPoolExecutor(max_workers=1)  # Single thread for Selenium

class ChapterSelectView(View):
    def __init__(self, chapters, ctx):
        super().__init__(timeout=300)
        self.chapters = chapters
        self.ctx = ctx
        self.selected_chapters = []

        options = [
            discord.SelectOption(label=title[:100], value=str(i))
            for i, (title, _) in enumerate(chapters)
        ]
        select = Select(
            placeholder="Select chapters to download...",
            options=options,
            min_values=1,
            max_values=len(chapters)
        )
        select.callback = self.select_callback
        self.add_item(select)

        button = Button(label="Download", style=discord.ButtonStyle.green)
        button.callback = self.download_callback
        self.add_item(button)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Only the command user can select chapters.", ephemeral=True)
            return
        self.selected_chapters = [self.chapters[int(i)] for i in interaction.data["values"]]
        await interaction.response.send_message(
            f"Selected {len(self.selected_chapters)} chapters. Click 'Download' to proceed.",
            ephemeral=True
        )

    async def download_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Only the command user can download.", ephemeral=True)
            return
        if not self.selected_chapters:
            await interaction.response.send_message("No chapters selected.", ephemeral=True)
            return
        await interaction.response.defer()
        # Offload EPUB creation to a thread
        future = executor.submit(create_epub, self.selected_chapters)
        try:
            epub_file = future.result(timeout=600)  # 10-minute timeout
            if epub_file:
                await interaction.followup.send(file=discord.File(epub_file, os.path.basename(epub_file)))
                os.remove(epub_file)
            else:
                await interaction.followup.send("Failed to create EPUB. Check logs for details.", ephemeral=True)
        except Exception as e:
            logging.error(f"Error in download_callback: {e}")
            await interaction.followup.send("An error occurred while creating the EPUB.", ephemeral=True)

@bot.command()
async def fetch(ctx, url: str):
    await ctx.send("Fetching chapters, please wait...")
    chapters = await fetch_chapters(url)
    if not chapters:
        await ctx.send("No chapters found.")
        return
    if len(chapters) > 20:
        chapters = chapters[:20]
    view = ChapterSelectView(chapters, ctx)
    await ctx.send("Select the chapters you want to download:", view=view)

async def fetch_chapters(url):
    browser = browser_manager.get_browser()
    try:
        browser.get(url)
        WebDriverWait(browser, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-tag='post-card']"))
        )
        soup = BeautifulSoup(browser.page_source, 'html.parser')
        cards = soup.select("div[data-tag='post-card']")
        chapters = []
        for card in cards:
            title_span = card.find('span', {'data-tag': 'post-title'})
            if title_span:
                chapter_link = title_span.find('a')
                if chapter_link:
                    title = chapter_link.text.strip()
                    url = chapter_link.get('href')
                    chapters.append((title, url))
        return chapters
    except Exception as e:
        logging.error(f"Error fetching chapters: {e}")
        return []

def fetch_chapter_content(browser, url):
    retries = 3
    for attempt in range(retries):
        try:
            full_url = f'https://www.patreon.com{url}'
            browser.get(full_url)
            wait = WebDriverWait(browser, 15)
            script_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'script#__NEXT_DATA__'))
            )
            script_content = script_element.get_attribute('textContent')
            json_data = json.loads(script_content)
            envelope = json_data['props']['pageProps']['bootstrapEnvelope']
            bootstrap = envelope.get('bootstrap') or envelope.get('pageBootstrap')
            if bootstrap and 'post' in bootstrap and 'data' in bootstrap['post']:
                attributes = bootstrap['post']['data']['attributes']
                if 'content' in attributes:
                    return attributes['content']
            logging.warning(f"No content found in JSON at {full_url}")
            return None
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed for URL {url}: {e}")
            # Debug: Log page source on failure
            if attempt == retries - 1:
                logging.error(f"Failed after {retries} attempts. Page source: {browser.page_source[:500]}...")
            time.sleep(2)
    return None

def sanitize_filename(filename):
    return re.sub(r'[^\w\s-]', '', filename).strip() or "untitled"

def generate_filename(chapters):
    if not chapters:
        return "empty_chapters"
    oldest = chapters[0][0]
    newest = chapters[-1][0]
    return f"{sanitize_filename(oldest[:15])}-{sanitize_filename(newest[:15])}.epub" if len(chapters) > 1 else f"{sanitize_filename(newest)}.epub"

def create_epub(chapters):
    browser = browser_manager.get_browser()
    try:
        book = epub.EpubBook()
        book.set_language("en")
        book.set_title("Patreon Chapters")
        reversed_chapters = list(reversed(chapters))
        epub_chapters = []

        for i, (title, url) in enumerate(reversed_chapters, start=1):
            logging.info(f"Fetching content for chapter: {title}")
            content = fetch_chapter_content(browser, url)
            if content:
                chapter = epub.EpubHtml(
                    title=title,
                    file_name=f'chap_{i:02}.xhtml',
                    lang='en'
                )
                chapter.content = f'<h1>{title}</h1><p>{content}</p>'.encode('utf-8')
                book.add_item(chapter)
                epub_chapters.append(chapter)
            else:
                logging.warning(f"No content fetched for chapter: {title}")

        if not epub_chapters:
            logging.error("No chapters with content to create EPUB")
            return None

        book.toc = tuple(epub_chapters)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ['nav'] + epub_chapters

        filename = generate_filename(reversed_chapters)
        temp_filepath = os.path.join(os.getcwd(), filename)
        epub.write_epub(temp_filepath, book)
        return temp_filepath
    except Exception as e:
        logging.error(f"Error creating EPUB: {e}")
        return None

@bot.event
async def on_close():
    browser_manager.shutdown()
    logging.info("Bot shutdown, browser closed")

# Run the bot
bot.run('YOUR_BOT_TOKEN')
