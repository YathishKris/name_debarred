from datetime import datetime
from app import db

class DownloadHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(10), nullable=False)  # NSE or BSE
    status = db.Column(db.String(20), nullable=False)  # success, failed
    entities_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<DownloadHistory {self.source} {self.timestamp}>'

class DebarredEntity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(10), nullable=False)  # NSE or BSE
    entity_id = db.Column(db.String(50), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    pan = db.Column(db.String(20), nullable=True)
    debarred_from = db.Column(db.Date, nullable=True)
    debarred_to = db.Column(db.Date, nullable=True)
    reason = db.Column(db.Text, nullable=True)
    order_details = db.Column(db.Text, nullable=True)
    details_url = db.Column(db.String(500), nullable=True)
    download_date = db.Column(db.Date, default=datetime.utcnow().date)
    
    # Composite unique constraint for source, name and entity_id to avoid duplicates
    __table_args__ = (
        db.UniqueConstraint('source', 'name', 'entity_id', name='_source_name_id_uc'),
    )
    
    def __repr__(self):
        return f'<DebarredEntity {self.source} {self.name}>'

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hour = db.Column(db.Integer, default=1)  # Hour to run daily job (24-hour format)
    minute = db.Column(db.Integer, default=0)  # Minute to run daily job
    retry_attempts = db.Column(db.Integer, default=3)  # Number of retry attempts
    retry_delay = db.Column(db.Integer, default=5)  # Delay between retries in minutes
    
    # Manual URL overrides
    use_manual_urls = db.Column(db.Boolean, default=False)  # Whether to use manual URLs
    nse_manual_url = db.Column(db.String(500), nullable=True)  # Manual URL for NSE data
    bse_manual_url = db.Column(db.String(500), nullable=True)  # Manual URL for BSE data
    
    def __repr__(self):
        return f'<Settings {self.hour}:{self.minute}>'
