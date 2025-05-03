import logging
import re
import json
import time
import requests
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from config import Config

logger = logging.getLogger(__name__)

class URLDiscovery:
    """
    Class to discover the current download URLs for debarred entities from NSE and BSE websites.
    Uses a combination of direct HTTP requests and headless browser automation.
    """
    
    @staticmethod
    def discover_nse_download_url():
        """
        Discover the download URL for debarred entities from NSE.
        NSE's API endpoints can be found by analyzing network requests on the page.
        
        Returns:
            str: The discovered download URL, or None if not found
        """
        logger.info("Discovering NSE download URL...")
        try:
            # First attempt: Try to get download link directly from the page
            headers = Config.get_headers()
            response = requests.get(
                urljoin(Config.NSE_BASE_URL, Config.NSE_DEBARRED_PAGE),
                headers=headers,
                timeout=Config.DOWNLOAD_TIMEOUT
            )
            response.raise_for_status()
            
            # Look for API endpoint in the page content
            content = response.text
            
            # NSE often loads data from an API endpoint that follows a pattern
            api_pattern = r'(\/api\/debarred-entities\/[a-zA-Z0-9\-\.\/]+)'
            match = re.search(api_pattern, content)
            
            if match:
                api_endpoint = match.group(1)
                download_url = urljoin(Config.NSE_BASE_URL, api_endpoint)
                logger.info(f"NSE download URL found: {download_url}")
                return download_url
                
            # If the direct approach fails, try using Selenium to extract the URL
            logger.info("Direct URL extraction failed, using Selenium for NSE...")
            return URLDiscovery._discover_nse_url_with_selenium()
            
        except requests.RequestException as e:
            logger.error(f"Error discovering NSE download URL: {str(e)}")
            # Fall back to Selenium if direct request fails
            return URLDiscovery._discover_nse_url_with_selenium()
        except Exception as e:
            logger.error(f"Unexpected error discovering NSE URL: {str(e)}")
            return None
    
    @staticmethod
    def _discover_nse_url_with_selenium():
        """
        Use headless Selenium to discover the NSE debarred entities download URL
        
        Returns:
            str: The discovered download URL, or None if not found
        """
        driver = None
        try:
            # Configure Chrome in headless mode
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={Config.USER_AGENT}")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(urljoin(Config.NSE_BASE_URL, Config.NSE_DEBARRED_PAGE))
            
            # Wait for the page to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Capture network requests to find the API endpoint
            # This is a complex task and might require additional JavaScript execution
            # For now, we'll try to find download button or API request in the page source
            page_source = driver.page_source
            
            # Look for download links or API endpoints
            api_pattern = r'(\/api\/debarred-entities\/[a-zA-Z0-9\-\.\/]+)'
            match = re.search(api_pattern, page_source)
            
            if match:
                api_endpoint = match.group(1)
                download_url = urljoin(Config.NSE_BASE_URL, api_endpoint)
                logger.info(f"NSE download URL found with Selenium: {download_url}")
                return download_url
            
            # If still no match, try to find a download button and get its URL
            try:
                download_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Download') or contains(@class, 'download')]"))
                )
                # Get the data-href attribute or onclick handler
                download_url = download_button.get_attribute("data-href") or download_button.get_attribute("onclick")
                
                if download_url:
                    # Extract the URL from the onclick handler if needed
                    url_in_onclick = re.search(r'[\'\"](\/[^\'\"]*)[\'\"]', download_url)
                    if url_in_onclick:
                        download_url = urljoin(Config.NSE_BASE_URL, url_in_onclick.group(1))
                        logger.info(f"NSE download URL extracted from button: {download_url}")
                        return download_url
            except (TimeoutException, NoSuchElementException) as e:
                logger.warning(f"Could not find download button: {str(e)}")
            
            # If we still don't have a URL, use the default API endpoint
            logger.warning("Using default NSE API endpoint as fallback")
            return urljoin(Config.NSE_BASE_URL, "/api/debarred-entities/getDebarredEntities")
            
        except WebDriverException as e:
            logger.error(f"Selenium error discovering NSE URL: {str(e)}")
            # Fallback to a typical API endpoint if all else fails
            return urljoin(Config.NSE_BASE_URL, "/api/debarred-entities/getDebarredEntities")
        finally:
            if driver:
                driver.quit()
    
    @staticmethod
    def discover_bse_download_url():
        """
        Discover the download URL for debarred entities from BSE.
        BSE might have AJAX calls to load the data or direct file download links.
        
        Returns:
            str: The discovered download URL, or None if not found
        """
        logger.info("Discovering BSE download URL...")
        try:
            # First try: direct page access
            headers = Config.get_headers()
            response = requests.get(
                urljoin(Config.BSE_BASE_URL, Config.BSE_DEBARRED_PAGE),
                headers=headers,
                timeout=Config.DOWNLOAD_TIMEOUT
            )
            response.raise_for_status()
            
            # Look for Excel/CSV download links in the page
            content = response.text
            excel_pattern = r'href=[\'\"](\/.*?\.(?:xlsx?|csv))[\'\"](.*?)[\'\"]*?'
            match = re.search(excel_pattern, content, re.IGNORECASE)
            
            if match:
                download_path = match.group(1)
                download_url = urljoin(Config.BSE_BASE_URL, download_path)
                logger.info(f"BSE download URL found: {download_url}")
                return download_url
            
            # If direct link not found, try to find AJAX endpoint
            ajax_pattern = r'url\s*:\s*[\'\"](\/.*?(?:ashx|asmx|aspx|svc)(?:\?.*?)?)[\'\"](.*?)[\'\"]*?'
            match = re.search(ajax_pattern, content)
            
            if match:
                ajax_url = match.group(1)
                download_url = urljoin(Config.BSE_BASE_URL, ajax_url)
                logger.info(f"BSE AJAX URL found: {download_url}")
                return download_url
                
            # If all fails, try Selenium approach
            logger.info("Direct URL extraction failed, using Selenium for BSE...")
            return URLDiscovery._discover_bse_url_with_selenium()
            
        except requests.RequestException as e:
            logger.error(f"Error discovering BSE download URL: {str(e)}")
            # Fall back to Selenium
            return URLDiscovery._discover_bse_url_with_selenium()
        except Exception as e:
            logger.error(f"Unexpected error discovering BSE URL: {str(e)}")
            return None
    
    @staticmethod
    def _discover_bse_url_with_selenium():
        """
        Use headless Selenium to discover the BSE debarred entities download URL
        
        Returns:
            str: The discovered download URL, or None if not found
        """
        driver = None
        try:
            # Configure Chrome in headless mode
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={Config.USER_AGENT}")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(urljoin(Config.BSE_BASE_URL, Config.BSE_DEBARRED_PAGE))
            
            # Wait for the page to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "dvAjaxLoad"))
            )
            
            # BSE often has download links with specific text or class
            try:
                # Look for download links
                download_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Download') or contains(@class, 'download')]")
                
                if download_links:
                    for link in download_links:
                        href = link.get_attribute("href")
                        if href and ('.xlsx' in href or '.xls' in href or '.csv' in href):
                            logger.info(f"BSE download URL found with Selenium: {href}")
                            return href
                
                # If no direct download links, look for export buttons
                export_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Export') or contains(@class, 'export')]")
                
                if export_buttons and len(export_buttons) > 0:
                    # Click the export button to trigger the download
                    export_buttons[0].click()
                    
                    # Wait for any AJAX calls to complete
                    time.sleep(3)
                    
                    # Check the network requests to find the download URL
                    page_source = driver.page_source
                    ajax_pattern = r'url\s*:\s*[\'\"](\/.*?(?:ashx|asmx|aspx|svc)(?:\?.*?)?)[\'\"](.*?)[\'\"]*?'
                    match = re.search(ajax_pattern, page_source)
                    
                    if match:
                        ajax_url = match.group(1)
                        download_url = urljoin(Config.BSE_BASE_URL, ajax_url)
                        logger.info(f"BSE AJAX URL found after clicking export: {download_url}")
                        return download_url
            except Exception as e:
                logger.error(f"Error finding download elements: {str(e)}")
            
            # If we still don't have a URL, check for any *.xlsx or *.csv links
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                href = link.get_attribute("href")
                if href and ('.xlsx' in href or '.xls' in href or '.csv' in href):
                    logger.info(f"BSE download URL found from all links: {href}")
                    return href
            
            # If all else fails, use a fallback default URL
            logger.warning("Using default BSE download URL as fallback")
            return urljoin(Config.BSE_BASE_URL, "/downloads/Debarred_entities.aspx")
            
        except WebDriverException as e:
            logger.error(f"Selenium error discovering BSE URL: {str(e)}")
            # Fallback to a typical download endpoint if all else fails
            return urljoin(Config.BSE_BASE_URL, "/downloads/Debarred_entities.aspx")
        finally:
            if driver:
                driver.quit()
