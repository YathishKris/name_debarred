import os
import logging
import time
import pandas as pd
import requests
from datetime import datetime
from flask import current_app
import traceback

from config import Config
from utils.url_discovery import URLDiscovery
from utils.data_processor import DataProcessor
from utils.demo_data import DemoDataGenerator
from models import DownloadHistory, DebarredEntity, Settings, db

logger = logging.getLogger(__name__)

class Downloader:
    """
    Class to download debarred entities data from NSE and BSE.
    Implements retry mechanism and error handling.
    """
    
    def __init__(self, app=None):
        """Initialize with Flask app context if provided"""
        self.app = app
    
    def download_nse_data(self):
        """
        Download debarred entities data from NSE
        
        Returns:
            tuple: (success, entity_count, error_message)
        """
        logger.info("Starting NSE data download...")
        
        # Get settings for retry
        settings = Settings.query.first()
        max_retries = settings.retry_attempts if settings else Config.MAX_RETRIES
        retry_delay = settings.retry_delay * 60 if settings else Config.RETRY_DELAY
        
        error_message = None
        entity_count = 0
        
        for attempt in range(max_retries):
            try:
                # Get the download URL
                download_url = URLDiscovery.discover_nse_download_url()
                if not download_url:
                    error_message = "Could not discover NSE download URL"
                    logger.error(error_message)
                    time.sleep(retry_delay)
                    continue
                
                # Download the data
                logger.info(f"Downloading from NSE URL: {download_url}")
                headers = Config.get_headers()
                response = requests.get(
                    download_url,
                    headers=headers,
                    timeout=Config.DOWNLOAD_TIMEOUT
                )
                response.raise_for_status()
                
                # Process the response based on content type
                content_type = response.headers.get('Content-Type', '').lower()
                
                # Create date string for file naming
                date_str = datetime.now().strftime("%Y%m%d")
                
                if 'json' in content_type:
                    # API response in JSON format
                    data = response.json()
                    
                    # Save raw data for backup
                    os.makedirs(Config.NSE_DATA_DIR, exist_ok=True)
                    json_file_path = os.path.join(Config.NSE_DATA_DIR, f"nse_debarred_{date_str}.json")
                    with open(json_file_path, 'w') as f:
                        f.write(response.text)
                    
                    # Process and save the data to database
                    entity_count = DataProcessor.process_nse_json_data(data)
                    
                    logger.info(f"Successfully downloaded and processed {entity_count} NSE entities")
                    return True, entity_count, None
                    
                elif 'excel' in content_type or 'spreadsheet' in content_type or 'csv' in content_type:
                    # Excel or CSV file
                    os.makedirs(Config.NSE_DATA_DIR, exist_ok=True)
                    
                    # Determine file extension from content type or URL
                    if 'excel' in content_type or 'spreadsheet' in content_type:
                        file_ext = '.xlsx'
                    elif 'csv' in content_type:
                        file_ext = '.csv'
                    else:
                        # Fallback to excel
                        file_ext = '.xlsx'
                    
                    file_path = os.path.join(Config.NSE_DATA_DIR, f"nse_debarred_{date_str}{file_ext}")
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Process and save the data
                    entity_count = DataProcessor.process_nse_file(file_path)
                    
                    logger.info(f"Successfully downloaded and processed {entity_count} NSE entities from file")
                    return True, entity_count, None
                    
                else:
                    # HTML or other format, try to extract table
                    logger.warning(f"Received unexpected content type: {content_type}")
                    
                    # Save the raw response for inspection
                    os.makedirs(Config.NSE_DATA_DIR, exist_ok=True)
                    html_file_path = os.path.join(Config.NSE_DATA_DIR, f"nse_debarred_{date_str}.html")
                    with open(html_file_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Try to extract tables from HTML
                    tables = pd.read_html(response.text)
                    if tables and len(tables) > 0:
                        # Save the first table as CSV
                        csv_file_path = os.path.join(Config.NSE_DATA_DIR, f"nse_debarred_{date_str}.csv")
                        tables[0].to_csv(csv_file_path, index=False)
                        
                        # Process and save the data
                        entity_count = DataProcessor.process_nse_file(csv_file_path)
                        
                        logger.info(f"Successfully extracted and processed {entity_count} NSE entities from HTML table")
                        return True, entity_count, None
                    else:
                        error_message = "No tables found in NSE response"
                        logger.error(error_message)
                        time.sleep(retry_delay)
                        continue
                
            except requests.RequestException as e:
                error_message = f"HTTP error downloading NSE data: {str(e)}"
                logger.error(error_message)
                time.sleep(retry_delay)
                continue
                
            except Exception as e:
                error_message = f"Error downloading NSE data: {str(e)}"
                logger.error(f"{error_message}\n{traceback.format_exc()}")
                time.sleep(retry_delay)
                continue
        
        # If we get here, all retries failed
        logger.error(f"All {max_retries} attempts to download NSE data failed")
        return False, entity_count, error_message
    
    def download_bse_data(self):
        """
        Download debarred entities data from BSE
        
        Returns:
            tuple: (success, entity_count, error_message)
        """
        logger.info("Starting BSE data download...")
        
        # Get settings for retry
        settings = Settings.query.first()
        max_retries = settings.retry_attempts if settings else Config.MAX_RETRIES
        retry_delay = settings.retry_delay * 60 if settings else Config.RETRY_DELAY
        
        error_message = None
        entity_count = 0
        
        for attempt in range(max_retries):
            try:
                # Get the download URL
                download_url = URLDiscovery.discover_bse_download_url()
                if not download_url:
                    error_message = "Could not discover BSE download URL"
                    logger.error(error_message)
                    time.sleep(retry_delay)
                    continue
                
                # Download the data
                logger.info(f"Downloading from BSE URL: {download_url}")
                headers = Config.get_headers()
                response = requests.get(
                    download_url,
                    headers=headers,
                    timeout=Config.DOWNLOAD_TIMEOUT
                )
                response.raise_for_status()
                
                # Process the response based on content type
                content_type = response.headers.get('Content-Type', '').lower()
                
                # Create date string for file naming
                date_str = datetime.now().strftime("%Y%m%d")
                
                if 'json' in content_type:
                    # API response in JSON format
                    data = response.json()
                    
                    # Save raw data for backup
                    os.makedirs(Config.BSE_DATA_DIR, exist_ok=True)
                    json_file_path = os.path.join(Config.BSE_DATA_DIR, f"bse_debarred_{date_str}.json")
                    with open(json_file_path, 'w') as f:
                        f.write(response.text)
                    
                    # Process and save the data to database
                    entity_count = DataProcessor.process_bse_json_data(data)
                    
                    logger.info(f"Successfully downloaded and processed {entity_count} BSE entities")
                    return True, entity_count, None
                    
                elif 'excel' in content_type or 'spreadsheet' in content_type or 'csv' in content_type:
                    # Excel or CSV file
                    os.makedirs(Config.BSE_DATA_DIR, exist_ok=True)
                    
                    # Determine file extension from content type or URL
                    if 'excel' in content_type or 'spreadsheet' in content_type:
                        file_ext = '.xlsx'
                    elif 'csv' in content_type:
                        file_ext = '.csv'
                    else:
                        # Fallback to excel
                        file_ext = '.xlsx'
                    
                    file_path = os.path.join(Config.BSE_DATA_DIR, f"bse_debarred_{date_str}{file_ext}")
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Process and save the data
                    entity_count = DataProcessor.process_bse_file(file_path)
                    
                    logger.info(f"Successfully downloaded and processed {entity_count} BSE entities from file")
                    return True, entity_count, None
                    
                else:
                    # HTML or other format, try to extract table
                    logger.warning(f"Received unexpected content type: {content_type}")
                    
                    # Save the raw response for inspection
                    os.makedirs(Config.BSE_DATA_DIR, exist_ok=True)
                    html_file_path = os.path.join(Config.BSE_DATA_DIR, f"bse_debarred_{date_str}.html")
                    with open(html_file_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Try to extract tables from HTML
                    tables = pd.read_html(response.text)
                    if tables and len(tables) > 0:
                        # Save the first table as CSV
                        csv_file_path = os.path.join(Config.BSE_DATA_DIR, f"bse_debarred_{date_str}.csv")
                        tables[0].to_csv(csv_file_path, index=False)
                        
                        # Process and save the data
                        entity_count = DataProcessor.process_bse_file(csv_file_path)
                        
                        logger.info(f"Successfully extracted and processed {entity_count} BSE entities from HTML table")
                        return True, entity_count, None
                    else:
                        error_message = "No tables found in BSE response"
                        logger.error(error_message)
                        time.sleep(retry_delay)
                        continue
                
            except requests.RequestException as e:
                error_message = f"HTTP error downloading BSE data: {str(e)}"
                logger.error(error_message)
                time.sleep(retry_delay)
                continue
                
            except Exception as e:
                error_message = f"Error downloading BSE data: {str(e)}"
                logger.error(f"{error_message}\n{traceback.format_exc()}")
                time.sleep(retry_delay)
                continue
        
        # If we get here, all retries failed
        logger.error(f"All {max_retries} attempts to download BSE data failed")
        return False, entity_count, error_message
        
# Function to be called by the scheduler
def run_download_job(app):
    """
    Run the download job for both NSE and BSE data
    """
    logger.info("Starting download job...")
    
    # Create necessary directories
    Config.create_directories()
    
    with app.app_context():
        # Check if we should use demo mode
        settings = Settings.query.first()
        use_demo_mode = settings and settings.use_demo_mode
        
        if use_demo_mode:
            logger.info("Using demo mode to generate sample data")
            
            # Generate demo NSE data
            try:
                nse_count = DemoDataGenerator.generate_nse_data()
                nse_success = True
                nse_error = None
                logger.info(f"Generated {nse_count} NSE demo entities")
            except Exception as e:
                nse_success = False
                nse_count = 0
                nse_error = f"Error generating NSE demo data: {str(e)}"
                logger.error(f"{nse_error}\n{traceback.format_exc()}")
            
            # Record NSE download history
            nse_history = DownloadHistory(
                source="NSE",
                status="success" if nse_success else "failed",
                entities_count=nse_count,
                error_message=nse_error
            )
            db.session.add(nse_history)
            db.session.commit()
            
            # Generate demo BSE data
            try:
                bse_count = DemoDataGenerator.generate_bse_data()
                bse_success = True
                bse_error = None
                logger.info(f"Generated {bse_count} BSE demo entities")
            except Exception as e:
                bse_success = False
                bse_count = 0
                bse_error = f"Error generating BSE demo data: {str(e)}"
                logger.error(f"{bse_error}\n{traceback.format_exc()}")
            
            # Record BSE download history
            bse_history = DownloadHistory(
                source="BSE",
                status="success" if bse_success else "failed",
                entities_count=bse_count,
                error_message=bse_error
            )
            db.session.add(bse_history)
            db.session.commit()
            
        else:
            # Use real download functionality
            downloader = Downloader(app)
            
            # Download NSE data
            nse_success, nse_count, nse_error = downloader.download_nse_data()
            
            # Record NSE download history
            nse_history = DownloadHistory(
                source="NSE",
                status="success" if nse_success else "failed",
                entities_count=nse_count,
                error_message=nse_error
            )
            db.session.add(nse_history)
            db.session.commit()
            
            # Download BSE data
            bse_success, bse_count, bse_error = downloader.download_bse_data()
            
            # Record BSE download history
            bse_history = DownloadHistory(
                source="BSE",
                status="success" if bse_success else "failed",
                entities_count=bse_count,
                error_message=bse_error
            )
            db.session.add(bse_history)
            db.session.commit()
        
        logger.info("Download job completed")
        
        return {
            "nse": {"success": nse_success, "count": nse_count, "error": nse_error},
            "bse": {"success": bse_success, "count": bse_count, "error": bse_error}
        }
