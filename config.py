import os
import logging

# Base configuration
class Config:
    # NSE and BSE base URLs
    NSE_BASE_URL = "https://www.nseindia.com"
    NSE_DEBARRED_PAGE = "/regulations/member-sebi-debarred-entities"
    
    BSE_BASE_URL = "https://www.bseindia.com"
    BSE_DEBARRED_PAGE = "/investors/debent.aspx?expandable=5"

    # Data storage paths
    DATA_DIR = "data"
    NSE_DATA_DIR = os.path.join(DATA_DIR, "nse")
    BSE_DATA_DIR = os.path.join(DATA_DIR, "bse")
    
    # Download settings
    DOWNLOAD_TIMEOUT = 60  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    # Logging configuration
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = logging.DEBUG
    
    # Create necessary directories
    @staticmethod
    def create_directories():
        os.makedirs(Config.NSE_DATA_DIR, exist_ok=True)
        os.makedirs(Config.BSE_DATA_DIR, exist_ok=True)
        
    # Request headers to use for HTTP requests
    @staticmethod
    def get_headers():
        return {
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
