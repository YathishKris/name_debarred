import os
import logging
import pandas as pd
import json
from datetime import datetime, date
from models import DebarredEntity, db

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Class to process downloaded data from NSE and BSE and store in database
    """
    
    @staticmethod
    def process_nse_json_data(data):
        """
        Process NSE debarred entities data in JSON format
        
        Args:
            data: JSON data from NSE API
            
        Returns:
            int: Number of entities processed
        """
        try:
            today = date.today()
            count = 0
            
            # NSE data structure may vary, handle different formats
            if isinstance(data, list):
                entities_list = data
            elif isinstance(data, dict):
                # Check common keys in NSE API responses
                if 'data' in data:
                    entities_list = data['data']
                elif 'entities' in data:
                    entities_list = data['entities']
                elif 'result' in data:
                    entities_list = data['result']
                else:
                    # If structure is unknown, log and return
                    logger.error(f"Unknown NSE JSON structure: {list(data.keys())}")
                    return 0
            else:
                logger.error(f"Unexpected NSE data type: {type(data)}")
                return 0
            
            # Process each entity
            for entity_data in entities_list:
                try:
                    # Map fields from NSE data to model
                    # Field names may vary, use common mappings
                    name = entity_data.get('name', entity_data.get('entityName', ''))
                    
                    # Skip if name is empty
                    if not name:
                        continue
                    
                    entity_id = entity_data.get('id', entity_data.get('entityId', ''))
                    pan = entity_data.get('pan', entity_data.get('panNumber', ''))
                    
                    # Convert date strings to date objects
                    try:
                        if 'fromDate' in entity_data or 'debarredFrom' in entity_data:
                            date_str = entity_data.get('fromDate', entity_data.get('debarredFrom', ''))
                            debarred_from = DataProcessor._parse_date(date_str)
                        else:
                            debarred_from = None
                            
                        if 'toDate' in entity_data or 'debarredTo' in entity_data:
                            date_str = entity_data.get('toDate', entity_data.get('debarredTo', ''))
                            debarred_to = DataProcessor._parse_date(date_str)
                        else:
                            debarred_to = None
                    except Exception as date_error:
                        logger.warning(f"Error parsing dates for entity {name}: {str(date_error)}")
                        debarred_from = None
                        debarred_to = None
                    
                    reason = entity_data.get('reason', entity_data.get('debarredReason', ''))
                    order_details = entity_data.get('orderDetails', entity_data.get('sebiOrderDetails', ''))
                    details_url = entity_data.get('detailsUrl', entity_data.get('orderUrl', ''))
                    
                    # Check if this entity already exists
                    existing_entity = DebarredEntity.query.filter_by(
                        source='NSE',
                        name=name,
                        entity_id=entity_id
                    ).first()
                    
                    if existing_entity:
                        # Update existing entity
                        existing_entity.pan = pan
                        existing_entity.debarred_from = debarred_from
                        existing_entity.debarred_to = debarred_to
                        existing_entity.reason = reason
                        existing_entity.order_details = order_details
                        existing_entity.details_url = details_url
                        existing_entity.download_date = today
                    else:
                        # Create new entity
                        new_entity = DebarredEntity(
                            source='NSE',
                            entity_id=entity_id,
                            name=name,
                            pan=pan,
                            debarred_from=debarred_from,
                            debarred_to=debarred_to,
                            reason=reason,
                            order_details=order_details,
                            details_url=details_url,
                            download_date=today
                        )
                        db.session.add(new_entity)
                    
                    count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing NSE entity: {str(e)}")
                    continue
            
            # Commit the changes to database
            db.session.commit()
            return count
            
        except Exception as e:
            logger.error(f"Error processing NSE JSON data: {str(e)}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def process_bse_json_data(data):
        """
        Process BSE debarred entities data in JSON format
        
        Args:
            data: JSON data from BSE API
            
        Returns:
            int: Number of entities processed
        """
        try:
            today = date.today()
            count = 0
            
            # BSE data structure may vary, handle different formats
            if isinstance(data, list):
                entities_list = data
            elif isinstance(data, dict):
                # Check common keys in BSE API responses
                if 'Table' in data:
                    entities_list = data['Table']
                elif 'data' in data:
                    entities_list = data['data']
                elif 'entities' in data:
                    entities_list = data['entities']
                elif 'result' in data:
                    entities_list = data['result']
                else:
                    # If structure is unknown, log and return
                    logger.error(f"Unknown BSE JSON structure: {list(data.keys())}")
                    return 0
            else:
                logger.error(f"Unexpected BSE data type: {type(data)}")
                return 0
            
            # Process each entity
            for entity_data in entities_list:
                try:
                    # Map fields from BSE data to model
                    # Field names may vary, use common mappings
                    name = entity_data.get('Name', entity_data.get('EntityName', ''))
                    
                    # Skip if name is empty
                    if not name:
                        continue
                    
                    entity_id = str(entity_data.get('ID', entity_data.get('EntityId', '')))
                    pan = entity_data.get('PAN', entity_data.get('PANNumber', ''))
                    
                    # Convert date strings to date objects
                    try:
                        if 'FromDate' in entity_data or 'DebarredFrom' in entity_data:
                            date_str = entity_data.get('FromDate', entity_data.get('DebarredFrom', ''))
                            debarred_from = DataProcessor._parse_date(date_str)
                        else:
                            debarred_from = None
                            
                        if 'ToDate' in entity_data or 'DebarredTo' in entity_data:
                            date_str = entity_data.get('ToDate', entity_data.get('DebarredTo', ''))
                            debarred_to = DataProcessor._parse_date(date_str)
                        else:
                            debarred_to = None
                    except Exception as date_error:
                        logger.warning(f"Error parsing dates for entity {name}: {str(date_error)}")
                        debarred_from = None
                        debarred_to = None
                    
                    reason = entity_data.get('Reason', entity_data.get('DebarredReason', ''))
                    order_details = entity_data.get('OrderDetails', entity_data.get('SEBIOrderDetails', ''))
                    details_url = entity_data.get('DetailsUrl', entity_data.get('OrderUrl', ''))
                    
                    # Check if this entity already exists
                    existing_entity = DebarredEntity.query.filter_by(
                        source='BSE',
                        name=name,
                        entity_id=entity_id
                    ).first()
                    
                    if existing_entity:
                        # Update existing entity
                        existing_entity.pan = pan
                        existing_entity.debarred_from = debarred_from
                        existing_entity.debarred_to = debarred_to
                        existing_entity.reason = reason
                        existing_entity.order_details = order_details
                        existing_entity.details_url = details_url
                        existing_entity.download_date = today
                    else:
                        # Create new entity
                        new_entity = DebarredEntity(
                            source='BSE',
                            entity_id=entity_id,
                            name=name,
                            pan=pan,
                            debarred_from=debarred_from,
                            debarred_to=debarred_to,
                            reason=reason,
                            order_details=order_details,
                            details_url=details_url,
                            download_date=today
                        )
                        db.session.add(new_entity)
                    
                    count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing BSE entity: {str(e)}")
                    continue
            
            # Commit the changes to database
            db.session.commit()
            return count
            
        except Exception as e:
            logger.error(f"Error processing BSE JSON data: {str(e)}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def process_nse_file(file_path):
        """
        Process NSE debarred entities data from Excel or CSV file
        
        Args:
            file_path: Path to the downloaded file
            
        Returns:
            int: Number of entities processed
        """
        try:
            today = date.today()
            
            # Read the file based on extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext == '.xlsx' or file_ext == '.xls':
                df = pd.read_excel(file_path)
            else:
                logger.error(f"Unsupported file extension: {file_ext}")
                return 0
            
            # Standardize column names to lowercase
            df.columns = [col.lower() for col in df.columns]
            
            # Map dataframe columns to model fields
            # Common column name mappings for NSE files
            name_col = next((col for col in df.columns if 'name' in col.lower()), None)
            id_col = next((col for col in df.columns if 'id' in col.lower() or 'no' in col.lower()), None)
            pan_col = next((col for col in df.columns if 'pan' in col.lower()), None)
            from_date_col = next((col for col in df.columns if 'from' in col.lower() or 'start' in col.lower()), None)
            to_date_col = next((col for col in df.columns if 'to' in col.lower() or 'end' in col.lower()), None)
            reason_col = next((col for col in df.columns if 'reason' in col.lower()), None)
            order_col = next((col for col in df.columns if 'order' in col.lower() or 'details' in col.lower()), None)
            url_col = next((col for col in df.columns if 'url' in col.lower() or 'link' in col.lower()), None)
            
            # Process each row
            count = 0
            for _, row in df.iterrows():
                try:
                    # Extract data from row
                    name = str(row[name_col]) if name_col and pd.notna(row[name_col]) else ""
                    
                    # Skip if name is empty
                    if not name or name.strip() == "":
                        continue
                    
                    entity_id = str(row[id_col]) if id_col and pd.notna(row[id_col]) else ""
                    pan = str(row[pan_col]) if pan_col and pd.notna(row[pan_col]) else ""
                    
                    # Parse dates
                    try:
                        debarred_from = DataProcessor._parse_date(row[from_date_col]) if from_date_col and pd.notna(row[from_date_col]) else None
                        debarred_to = DataProcessor._parse_date(row[to_date_col]) if to_date_col and pd.notna(row[to_date_col]) else None
                    except Exception as date_error:
                        logger.warning(f"Error parsing dates for entity {name}: {str(date_error)}")
                        debarred_from = None
                        debarred_to = None
                    
                    reason = str(row[reason_col]) if reason_col and pd.notna(row[reason_col]) else ""
                    order_details = str(row[order_col]) if order_col and pd.notna(row[order_col]) else ""
                    details_url = str(row[url_col]) if url_col and pd.notna(row[url_col]) else ""
                    
                    # Check if this entity already exists
                    existing_entity = DebarredEntity.query.filter_by(
                        source='NSE',
                        name=name,
                        entity_id=entity_id
                    ).first()
                    
                    if existing_entity:
                        # Update existing entity
                        existing_entity.pan = pan
                        existing_entity.debarred_from = debarred_from
                        existing_entity.debarred_to = debarred_to
                        existing_entity.reason = reason
                        existing_entity.order_details = order_details
                        existing_entity.details_url = details_url
                        existing_entity.download_date = today
                    else:
                        # Create new entity
                        new_entity = DebarredEntity(
                            source='NSE',
                            entity_id=entity_id,
                            name=name,
                            pan=pan,
                            debarred_from=debarred_from,
                            debarred_to=debarred_to,
                            reason=reason,
                            order_details=order_details,
                            details_url=details_url,
                            download_date=today
                        )
                        db.session.add(new_entity)
                    
                    count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing NSE file row: {str(e)}")
                    continue
            
            # Commit the changes to database
            db.session.commit()
            return count
            
        except Exception as e:
            logger.error(f"Error processing NSE file data: {str(e)}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def process_bse_file(file_path):
        """
        Process BSE debarred entities data from Excel or CSV file
        
        Args:
            file_path: Path to the downloaded file
            
        Returns:
            int: Number of entities processed
        """
        try:
            today = date.today()
            
            # Read the file based on extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext == '.xlsx' or file_ext == '.xls':
                df = pd.read_excel(file_path)
            else:
                logger.error(f"Unsupported file extension: {file_ext}")
                return 0
            
            # Standardize column names to lowercase
            df.columns = [col.lower() for col in df.columns]
            
            # Map dataframe columns to model fields
            # Common column name mappings for BSE files
            name_col = next((col for col in df.columns if 'name' in col.lower()), None)
            id_col = next((col for col in df.columns if 'id' in col.lower() or 'no' in col.lower() or 'sr' in col.lower()), None)
            pan_col = next((col for col in df.columns if 'pan' in col.lower()), None)
            from_date_col = next((col for col in df.columns if 'from' in col.lower() or 'start' in col.lower()), None)
            to_date_col = next((col for col in df.columns if 'to' in col.lower() or 'end' in col.lower()), None)
            reason_col = next((col for col in df.columns if 'reason' in col.lower()), None)
            order_col = next((col for col in df.columns if 'order' in col.lower() or 'details' in col.lower()), None)
            url_col = next((col for col in df.columns if 'url' in col.lower() or 'link' in col.lower()), None)
            
            # Process each row
            count = 0
            for _, row in df.iterrows():
                try:
                    # Extract data from row
                    name = str(row[name_col]) if name_col and pd.notna(row[name_col]) else ""
                    
                    # Skip if name is empty
                    if not name or name.strip() == "":
                        continue
                    
                    entity_id = str(row[id_col]) if id_col and pd.notna(row[id_col]) else ""
                    pan = str(row[pan_col]) if pan_col and pd.notna(row[pan_col]) else ""
                    
                    # Parse dates
                    try:
                        debarred_from = DataProcessor._parse_date(row[from_date_col]) if from_date_col and pd.notna(row[from_date_col]) else None
                        debarred_to = DataProcessor._parse_date(row[to_date_col]) if to_date_col and pd.notna(row[to_date_col]) else None
                    except Exception as date_error:
                        logger.warning(f"Error parsing dates for entity {name}: {str(date_error)}")
                        debarred_from = None
                        debarred_to = None
                    
                    reason = str(row[reason_col]) if reason_col and pd.notna(row[reason_col]) else ""
                    order_details = str(row[order_col]) if order_col and pd.notna(row[order_col]) else ""
                    details_url = str(row[url_col]) if url_col and pd.notna(row[url_col]) else ""
                    
                    # Check if this entity already exists
                    existing_entity = DebarredEntity.query.filter_by(
                        source='BSE',
                        name=name,
                        entity_id=entity_id
                    ).first()
                    
                    if existing_entity:
                        # Update existing entity
                        existing_entity.pan = pan
                        existing_entity.debarred_from = debarred_from
                        existing_entity.debarred_to = debarred_to
                        existing_entity.reason = reason
                        existing_entity.order_details = order_details
                        existing_entity.details_url = details_url
                        existing_entity.download_date = today
                    else:
                        # Create new entity
                        new_entity = DebarredEntity(
                            source='BSE',
                            entity_id=entity_id,
                            name=name,
                            pan=pan,
                            debarred_from=debarred_from,
                            debarred_to=debarred_to,
                            reason=reason,
                            order_details=order_details,
                            details_url=details_url,
                            download_date=today
                        )
                        db.session.add(new_entity)
                    
                    count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing BSE file row: {str(e)}")
                    continue
            
            # Commit the changes to database
            db.session.commit()
            return count
            
        except Exception as e:
            logger.error(f"Error processing BSE file data: {str(e)}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def _parse_date(date_str):
        """
        Parse date string in various formats
        
        Args:
            date_str: Date string to parse
            
        Returns:
            datetime.date: Parsed date or None if parsing fails
        """
        if not date_str or pd.isna(date_str):
            return None
            
        # Convert date_str to string if it's not already
        if not isinstance(date_str, str):
            date_str = str(date_str)
            
        # Remove any extra whitespace
        date_str = date_str.strip()
        
        # If empty after stripping, return None
        if not date_str:
            return None
            
        # Try various date formats
        date_formats = [
            '%Y-%m-%d',  # ISO format
            '%d-%m-%Y',  # DD-MM-YYYY
            '%d/%m/%Y',  # DD/MM/YYYY
            '%m/%d/%Y',  # MM/DD/YYYY
            '%d.%m.%Y',  # DD.MM.YYYY
            '%Y/%m/%d',  # YYYY/MM/DD
            '%b %d, %Y',  # Jan 31, 2022
            '%d %b %Y',   # 31 Jan 2022
            '%d-%b-%Y',   # 31-Jan-2022
            '%d %b, %Y',  # 31 Jan, 2022
            '%B %d, %Y',  # January 31, 2022
            '%d %B %Y',   # 31 January 2022
            '%d-%B-%Y',   # 31-January-2022
            '%d %B, %Y',  # 31 January, 2022
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                return parsed_date
            except ValueError:
                continue
                
        # If all formats fail, try pandas to_datetime
        try:
            return pd.to_datetime(date_str).date()
        except Exception:
            # If all parsing attempts fail, log and return None
            logger.warning(f"Could not parse date string: {date_str}")
            return None
