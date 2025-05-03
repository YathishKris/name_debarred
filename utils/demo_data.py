import logging
import json
import os
import random
from datetime import datetime, timedelta
from config import Config
from models import DebarredEntity, db

logger = logging.getLogger(__name__)

class DemoDataGenerator:
    """
    Generate sample data for demo mode
    """
    
    @staticmethod
    def generate_nse_data():
        """
        Generate sample NSE debarred entities data
        
        Returns:
            int: Number of entities generated
        """
        logger.info("Generating sample NSE data for demo mode")
        
        # Sample NSE entity names and details
        nse_entities = [
            {
                "name": "Aarav Securities Pvt Ltd",
                "entity_id": "NSE0001",
                "pan": "ABCDE1234F",
                "debarred_from": datetime.now().date() - timedelta(days=365),
                "debarred_to": datetime.now().date() + timedelta(days=365),
                "reason": "Violation of market rules and manipulative trading practices",
                "order_details": "SEBI Order No: WTM/AB/IVD/ID2/7429/2022-23",
                "details_url": "https://www.nseindia.com/regulations/member-sebi-debarred-entities/details/NSE0001"
            },
            {
                "name": "Prisha Investments",
                "entity_id": "NSE0002",
                "pan": "FGHIJ5678K",
                "debarred_from": datetime.now().date() - timedelta(days=180),
                "debarred_to": datetime.now().date() + timedelta(days=730),
                "reason": "Fraudulent trading activities and misrepresentation",
                "order_details": "SEBI Order No: WTM/CD/IVD/ID4/9876/2022-23",
                "details_url": "https://www.nseindia.com/regulations/member-sebi-debarred-entities/details/NSE0002"
            },
            {
                "name": "Vihaan Capital Management",
                "entity_id": "NSE0003",
                "pan": "KLMNO9012P",
                "debarred_from": datetime.now().date() - timedelta(days=90),
                "debarred_to": datetime.now().date() + timedelta(days=545),
                "reason": "Non-compliance with regulatory requirements",
                "order_details": "SEBI Order No: WTM/EF/IVD/ID1/5432/2023-24",
                "details_url": "https://www.nseindia.com/regulations/member-sebi-debarred-entities/details/NSE0003"
            },
            {
                "name": "Advait Brokerage Solutions",
                "entity_id": "NSE0004",
                "pan": "QRSTU3456V",
                "debarred_from": datetime.now().date() - timedelta(days=120),
                "debarred_to": datetime.now().date() + timedelta(days=455),
                "reason": "Unauthorized trading and client fund misappropriation",
                "order_details": "SEBI Order No: WTM/GH/IVD/ID3/1234/2023-24",
                "details_url": "https://www.nseindia.com/regulations/member-sebi-debarred-entities/details/NSE0004"
            },
            {
                "name": "Riya Market Makers",
                "entity_id": "NSE0005",
                "pan": "VWXYZ7890A",
                "debarred_from": datetime.now().date() - timedelta(days=30),
                "debarred_to": datetime.now().date() + timedelta(days=180),
                "reason": "Front-running and insider trading violations",
                "order_details": "SEBI Order No: WTM/IJ/IVD/ID6/6789/2023-24",
                "details_url": "https://www.nseindia.com/regulations/member-sebi-debarred-entities/details/NSE0005"
            }
        ]
        
        # Save generated data to file for reference
        try:
            os.makedirs(Config.NSE_DATA_DIR, exist_ok=True)
            date_str = datetime.now().strftime("%Y%m%d")
            json_file_path = os.path.join(Config.NSE_DATA_DIR, f"nse_debarred_{date_str}_demo.json")
            
            with open(json_file_path, 'w') as f:
                json.dump({"entities": nse_entities}, f, indent=2, default=str)
            
            logger.info(f"Saved demo NSE data to {json_file_path}")
        except Exception as e:
            logger.error(f"Error saving demo NSE data: {str(e)}")
        
        # Add to database (avoiding duplicates)
        try:
            count = 0
            for entity in nse_entities:
                # Check if entity already exists
                existing = DebarredEntity.query.filter_by(
                    source="NSE", 
                    entity_id=entity["entity_id"]
                ).first()
                
                if not existing:
                    # Add new entity
                    new_entity = DebarredEntity(
                        source="NSE",
                        entity_id=entity["entity_id"],
                        name=entity["name"],
                        pan=entity["pan"],
                        debarred_from=entity["debarred_from"],
                        debarred_to=entity["debarred_to"],
                        reason=entity["reason"],
                        order_details=entity["order_details"],
                        details_url=entity["details_url"],
                        download_date=datetime.now().date()
                    )
                    db.session.add(new_entity)
                    count += 1
            
            db.session.commit()
            logger.info(f"Added {count} new NSE demo entities to database")
            return count
            
        except Exception as e:
            logger.error(f"Error adding NSE demo entities to database: {str(e)}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def generate_bse_data():
        """
        Generate sample BSE debarred entities data
        
        Returns:
            int: Number of entities generated
        """
        logger.info("Generating sample BSE data for demo mode")
        
        # Sample BSE entity names and details
        bse_entities = [
            {
                "name": "Arjun Financial Services",
                "entity_id": "BSE0001",
                "pan": "BCDEF2345G",
                "debarred_from": datetime.now().date() - timedelta(days=400),
                "debarred_to": datetime.now().date() + timedelta(days=300),
                "reason": "Market manipulation and unfair trading practices",
                "order_details": "SEBI Order No: SEBI/WTM/SR/BM/124/04/2022",
                "details_url": "https://www.bseindia.com/investors/debent/details/BSE0001"
            },
            {
                "name": "Saanvi Securities Ltd",
                "entity_id": "BSE0002",
                "pan": "GHIJK6789L",
                "debarred_from": datetime.now().date() - timedelta(days=200),
                "debarred_to": datetime.now().date() + timedelta(days=500),
                "reason": "Non-compliance with KYC norms and client fund misuse",
                "order_details": "SEBI Order No: SEBI/WTM/JK/BM/234/06/2022",
                "details_url": "https://www.bseindia.com/investors/debent/details/BSE0002"
            },
            {
                "name": "Reyansh Broking Pvt Ltd",
                "entity_id": "BSE0003",
                "pan": "LMNOP0123Q",
                "debarred_from": datetime.now().date() - timedelta(days=150),
                "debarred_to": datetime.now().date() + timedelta(days=600),
                "reason": "Unauthorized trading and client securities misappropriation",
                "order_details": "SEBI Order No: SEBI/WTM/PQ/BM/345/08/2022",
                "details_url": "https://www.bseindia.com/investors/debent/details/BSE0003"
            },
            {
                "name": "Aadhya Stock Brokers",
                "entity_id": "BSE0004",
                "pan": "QRSTU4567V",
                "debarred_from": datetime.now().date() - timedelta(days=75),
                "debarred_to": datetime.now().date() + timedelta(days=385),
                "reason": "Failure to redress investor grievances and regulatory violations",
                "order_details": "SEBI Order No: SEBI/WTM/RS/BM/456/10/2022",
                "details_url": "https://www.bseindia.com/investors/debent/details/BSE0004"
            },
            {
                "name": "Dhruv Investments & Securities",
                "entity_id": "BSE0005",
                "pan": "VWXYZ8901B",
                "debarred_from": datetime.now().date() - timedelta(days=45),
                "debarred_to": datetime.now().date() + timedelta(days=275),
                "reason": "Insider trading and fraudulent trade practices",
                "order_details": "SEBI Order No: SEBI/WTM/TU/BM/567/12/2022",
                "details_url": "https://www.bseindia.com/investors/debent/details/BSE0005"
            }
        ]
        
        # Save generated data to file for reference
        try:
            os.makedirs(Config.BSE_DATA_DIR, exist_ok=True)
            date_str = datetime.now().strftime("%Y%m%d")
            json_file_path = os.path.join(Config.BSE_DATA_DIR, f"bse_debarred_{date_str}_demo.json")
            
            with open(json_file_path, 'w') as f:
                json.dump({"entities": bse_entities}, f, indent=2, default=str)
            
            logger.info(f"Saved demo BSE data to {json_file_path}")
        except Exception as e:
            logger.error(f"Error saving demo BSE data: {str(e)}")
        
        # Add to database (avoiding duplicates)
        try:
            count = 0
            for entity in bse_entities:
                # Check if entity already exists
                existing = DebarredEntity.query.filter_by(
                    source="BSE", 
                    entity_id=entity["entity_id"]
                ).first()
                
                if not existing:
                    # Add new entity
                    new_entity = DebarredEntity(
                        source="BSE",
                        entity_id=entity["entity_id"],
                        name=entity["name"],
                        pan=entity["pan"],
                        debarred_from=entity["debarred_from"],
                        debarred_to=entity["debarred_to"],
                        reason=entity["reason"],
                        order_details=entity["order_details"],
                        details_url=entity["details_url"],
                        download_date=datetime.now().date()
                    )
                    db.session.add(new_entity)
                    count += 1
            
            db.session.commit()
            logger.info(f"Added {count} new BSE demo entities to database")
            return count
            
        except Exception as e:
            logger.error(f"Error adding BSE demo entities to database: {str(e)}")
            db.session.rollback()
            return 0