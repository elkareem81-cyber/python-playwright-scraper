# Python Flipbook Image Extractor (Playwright)

A powerful, asynchronous web scraping script designed to log into a secure student portal and extract all page images from a 'flipbook' style e-book.

This script was originally built to archive educational materials from a specific university portal but can be adapted for any website that uses:
* A login form (email/password).
* A 'flipbook' that loads page images as `data:image/base64,...` URIs.
* A "Next" button or arrow key navigation.

## 🚀 Features

* **Secure Login:** Handles authentication using environment variables (credentials are never hard-coded).
* **Asynchronous Scraping:** Uses `asyncio` and `playwright` for efficient, non-blocking page interactions.
* **Smart Extraction:** Locates all `<img>` tags within the flipbook element.
* **Base64 Decoding:** Automatically decodes `data:image/...;base64` strings and saves them as valid `.webp` or `.png` files.
* **Duplicate Prevention:** Uses a `set()` to track saved image sources, preventing duplicate downloads.
* **Auto-Stop:** Intelligently stops the script after a set number of clicks with no new images found.

## 🛠 Tech Stack

* **Python 3**
* **Playwright:** For browser automation and page interaction.
* **Pillow (PIL):** For processing and saving the decoded image data.
* **Asyncio:** For handling asynchronous operations.

## ⚙️ How to Run

### 1. Clone or Download
Download the `extract_pages_playwright.py` script to your local machine.

### 2. Install Dependencies
You need Python 3, Playwright, and Pillow.
```bash
# Install required Python libraries
pip install playwright pillow

# Install the browser binaries (e.g., chromium)
playwright install chromium
