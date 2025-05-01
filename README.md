# 1688 Product Data Workflow Automation

A workflow automation system for scraping, processing, translating, and storing product data from 1688.com.

## Overview

This project automates the following process:
1. Retrieves product URLs from a Notion database
2. Scrapes product information from 1688.com
3. Downloads product images
4. Extracts text from images using OCR
5. Translates Chinese text to English
6. Uploads processed data to Google Drive
7. Updates the Notion database with links to the processed data

## Prerequisites

- Python 3.9+
- Google Chrome (for web scraping)
- Google Drive API credentials
- Notion API credentials
- OpenAI API key
- (Optional) Oxylabs proxy credentials

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd 1688-scraper
```

### 2. Set up environment variables

Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

Edit the `.env` file with your API keys and configuration:

```ini
# API credentials
OPENAI_API_KEY=your_openai_api_key_here
NOTION_BEARER_TOKEN=your_notion_token_here
NOTION_DB_ID=your_notion_database_id_here

# (Optional) Proxy configuration
OXYLABS_USERNAME=your_oxylabs_username
OXYLABS_PASSWORD=your_oxylabs_password
OXYLABS_ENDPOINT=pr.oxylabs.io:7777
```

### 3. Google Drive Setup

1. Create a project in the [Google Developers Console](https://console.developers.google.com/)
2. Enable the Google Drive API
3. Create OAuth 2.0 credentials
4. Download the credentials as JSON and save it as `client_secrets.json` in the project root

### 4. Docker Deployment

The easiest way to run the project is using Docker:

```bash
# Build and start the container
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 5. Manual Installation (Alternative to Docker)

If you prefer to run without Docker:

1. Install system dependencies:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python main.py
```

## Project Structure

```
project_root/
├── integrations/        # API integrations
├── llm/                 # Translation services
├── ocr/                 # OCR processing
├── utils/               # Utility functions
├── logs/                # Log files
├── output/              # Output files
│   └── images/          # Downloaded images
├── docker-compose.yml   # Docker configuration
├── Dockerfile           # Docker build file
├── main.py              # Main entry point
├── parser.py            # HTML parsing logic
└── scraper.py           # Web scraping logic
```

## Configuration Options

The project can be configured through environment variables in the `.env` file:

- `ENV`: Set to `dev` for local development or `prod` for production
- `HEADLESS`: Set to `True` to run Chrome in headless mode
- `TRANSLATION_MODEL`: OpenAI model to use for translation (default: `gpt-3.5-turbo`)
- `LOCAL_DB`: Filename for the SQLite database
- `LOCAL_OUTPUT_FOLDER`: Path to store downloaded files
- `GD_OUTPUT_FOLDER`: Google Drive folder name for uploaded files

## Troubleshooting

### Google Drive Authentication

If you encounter issues with Google Drive authentication:

1. Delete the `mycreds.txt` file (if it exists)
2. Run the application locally (not in Docker)
3. Complete the OAuth flow in your browser
4. The new credentials will be saved in `mycreds.txt`
5. Deploy with Docker, mounting the `mycreds.txt` file

### Proxy Issues

If you're having trouble with site access:

1. Update your Oxylabs credentials in the `.env` file
2. Uncomment the proxy configuration in `media_downloader.py`
3. Try different proxy endpoints if necessary

### Database Lock Errors

If you see "database is locked" errors:

1. Stop all instances of the application
2. Check for any processes using the database
3. If necessary, restore from a backup of the `.db` file
