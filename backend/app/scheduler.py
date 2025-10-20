import logging
from datetime import datetime
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .db.session import SessionLocal
from . import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_expired_licenses():
    """
    Job to periodically check for expired licenses and update their status.
    """
    logger.info("Scheduler job 'update_expired_licenses' starting...")
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        expired_licenses = db.query(models.License).filter(
            models.License.status == 'active',
            models.License.expires_at < now
        ).all()

        if not expired_licenses:
            logger.info("No expired licenses found.")
            return

        logger.info(f"Found {len(expired_licenses)} expired licenses to update.")
        for license in expired_licenses:
            license.status = 'expired'
            db.add(license)
        
        db.commit()
        logger.info("Successfully updated status for expired licenses.")

    except Exception as e:
        logger.error(f"Error in 'update_expired_licenses' job: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

# Initialize scheduler
scheduler = BackgroundScheduler(daemon=True)

# Schedule the job to run once every day at midnight
scheduler.add_job(
    update_expired_licenses,
    trigger=CronTrigger(hour=0, minute=0),
    id="update_expired_licenses_job",
    name="Update expired licenses status daily",
    replace_existing=True,
)