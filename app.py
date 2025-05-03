import os
import logging
import traceback
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import Config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database - using PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Import after db is defined to avoid circular imports
from models import DownloadHistory, DebarredEntity, Settings
from utils.downloader import run_download_job

# Initialize the scheduler
scheduler = BackgroundScheduler()

def initialize_scheduler():
    # Clear existing jobs
    scheduler.remove_all_jobs()
    
    with app.app_context():
        settings = Settings.query.first()
        if settings:
            # Schedule the download job based on settings
            scheduler.add_job(
                run_download_job,
                trigger=CronTrigger(hour=settings.hour, minute=settings.minute),
                id='download_job',
                replace_existing=True,
                args=[app]
            )
            logger.info(f"Scheduled download job for {settings.hour}:{settings.minute}")
        else:
            # Default schedule at 1:00 AM if no settings exist
            scheduler.add_job(
                run_download_job,
                trigger=CronTrigger(hour=1, minute=0),
                id='download_job',
                replace_existing=True,
                args=[app]
            )
            logger.info("Scheduled download job with default timing (1:00 AM)")

@app.route('/')
def index():
    # Get the most recent downloads
    recent_downloads = DownloadHistory.query.order_by(DownloadHistory.timestamp.desc()).limit(5).all()
    
    # Count entities
    nse_count = DebarredEntity.query.filter_by(source='NSE').count()
    bse_count = DebarredEntity.query.filter_by(source='BSE').count()
    
    # Get the next scheduled run time
    next_run = None
    job = scheduler.get_job('download_job')
    if job and hasattr(job, 'next_run_time'):
        next_run = job.next_run_time
    
    settings = Settings.query.first()
    
    return render_template(
        'index.html', 
        recent_downloads=recent_downloads,
        nse_count=nse_count,
        bse_count=bse_count,
        next_run=next_run,
        settings=settings
    )

@app.route('/run-now', methods=['POST'])
def run_now():
    try:
        # Run the download job immediately
        logger.info("Manual download job triggered by user")
        
        # Create necessary directories
        Config.create_directories()
        
        result = run_download_job(app)
        
        if result:
            nse_result = result.get('nse', {})
            bse_result = result.get('bse', {})
            
            nse_success = nse_result.get('success', False)
            bse_success = bse_result.get('success', False)
            
            nse_count = nse_result.get('count', 0)
            bse_count = bse_result.get('count', 0)
            
            total_count = nse_count + bse_count
            
            if nse_success and bse_success:
                flash(f'Download job completed successfully! Downloaded {total_count} entities.', 'success')
            elif nse_success:
                flash(f'NSE download succeeded ({nse_count} entities), but BSE download failed: {bse_result.get("error")}', 'warning')
            elif bse_success:
                flash(f'BSE download succeeded ({bse_count} entities), but NSE download failed: {nse_result.get("error")}', 'warning')
            else:
                flash(f'Download job failed. NSE error: {nse_result.get("error")}. BSE error: {bse_result.get("error")}', 'danger')
        else:
            flash('Download job completed but returned no results.', 'warning')
            
    except Exception as e:
        logger.error(f"Error running job manually: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Error running job: {str(e)}', 'danger')
        
    return redirect(url_for('index'))

@app.route('/history')
def history():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get paginated download history
    downloads = DownloadHistory.query.order_by(
        DownloadHistory.timestamp.desc()
    ).paginate(page=page, per_page=per_page)
    
    return render_template('history.html', downloads=downloads)

@app.route('/report')
def report():
    source = request.args.get('source', 'all')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = DebarredEntity.query
    
    # Apply filters
    if source and source != 'all':
        query = query.filter_by(source=source)
    
    if date_from:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(DebarredEntity.download_date >= date_from_obj)
    
    if date_to:
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        query = query.filter(DebarredEntity.download_date <= date_to_obj)
    
    # Get paginated results
    page = request.args.get('page', 1, type=int)
    per_page = 50
    entities = query.order_by(DebarredEntity.download_date.desc()).paginate(page=page, per_page=per_page)
    
    # Get unique sources for filter dropdown
    sources = db.session.query(DebarredEntity.source).distinct().all()
    source_list = [s[0] for s in sources]
    
    return render_template(
        'report.html', 
        entities=entities, 
        sources=source_list,
        current_source=source,
        date_from=date_from,
        date_to=date_to
    )

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        try:
            hour = int(request.form.get('hour', 1))
            minute = int(request.form.get('minute', 0))
            retry_attempts = int(request.form.get('retry_attempts', 3))
            retry_delay = int(request.form.get('retry_delay', 5))
            
            # Handle manual URL settings
            use_manual_urls = request.form.get('use_manual_urls') == 'true'
            nse_manual_url = request.form.get('nse_manual_url', '').strip()
            bse_manual_url = request.form.get('bse_manual_url', '').strip()
            
            settings = Settings.query.first()
            if not settings:
                settings = Settings()
                db.session.add(settings)
            
            settings.hour = hour
            settings.minute = minute
            settings.retry_attempts = retry_attempts
            settings.retry_delay = retry_delay
            
            # Update manual URL settings
            settings.use_manual_urls = use_manual_urls
            settings.nse_manual_url = nse_manual_url
            settings.bse_manual_url = bse_manual_url
            
            db.session.commit()
            
            # Reinitialize scheduler with new settings
            initialize_scheduler()
            
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('settings'))
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            flash(f'Error updating settings: {str(e)}', 'danger')
    
    settings = Settings.query.first()
    return render_template('settings.html', settings=settings)

# Initialize database tables and scheduler on startup
with app.app_context():
    db.create_all()
    
    # Create default settings if none exist
    if not Settings.query.first():
        default_settings = Settings(
            hour=1,
            minute=0,
            retry_attempts=3,
            retry_delay=5
        )
        db.session.add(default_settings)
        db.session.commit()
    
    # Initialize the scheduler
    initialize_scheduler()

# Add context processor for templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Start the scheduler
scheduler.start()

# Register cleanup on app shutdown
@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    if scheduler.running:
        scheduler.shutdown()
