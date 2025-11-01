"""
Celery application and background tasks.

This module sets up Celery for background task processing.
Main tasks include:
- Automatic cleanup of unverified users after 2 days
- Email/SMS sending (in production)
"""

import asyncio

from celery import Celery
from celery.schedules import crontab

from src.core.config import settings
from src.core.database import async_session_factory
from src.repositories.user_repository import UserRepository

# Create Celery instance
celery_app = Celery("coffeeshop", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    "cleanup-unverified-users": {
        "task": "src.tasks.celery_app.cleanup_unverified_users",
        "schedule": crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}


@celery_app.task(name="src.tasks.celery_app.cleanup_unverified_users")
def cleanup_unverified_users():
    """
    Periodic task to clean up unverified users.

    This task runs daily and removes users who:
    - Have not verified their account
    - Were created more than 2 days ago (configurable)

    Note: This is implemented as a sync function because Celery
    doesn't natively support async tasks in all configurations.
    For production, consider using celery-aio or running async
    code with asyncio.run().
    """

    async def cleanup():
        """Async function to perform cleanup."""
        async with async_session_factory() as session:
            async with session.begin():
                user_repo = UserRepository(session)

                # Get unverified users older than configured days
                unverified_users = await user_repo.get_unverified_users_older_than(
                    days=settings.UNVERIFIED_USER_DELETE_DAYS
                )

                if not unverified_users:
                    print("✅ No unverified users to clean up")
                    return 0

                # Delete users in a single atomic transaction
                deleted_count = await user_repo.bulk_delete(unverified_users)

                print(f"🗑️  Cleaned up {deleted_count} unverified users")

                # Log deleted emails for audit
                for user in unverified_users:
                    print(f"   - Deleted: {user.email} (created: {user.created_at})")

                return deleted_count
            # Transaction automatically commits when exiting session.begin() context

    # Run async cleanup
    try:
        deleted_count = asyncio.run(cleanup())
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"Successfully cleaned up {deleted_count} unverified users",
        }
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="src.tasks.celery_app.send_verification_email")
def send_verification_email(email: str, code: str):
    # TODO: Implement actual email sending
    print(f"📧 Sending verification email to {email} with code {code}")

    return {"status": "sent", "email": email}


@celery_app.task(name="src.tasks.celery_app.send_verification_sms")
def send_verification_sms(phone: str, code: str):
    # TODO: Implement actual SMS sending
    print(f"📱 Sending verification SMS to {phone} with code {code}")

    return {"status": "sent", "phone": phone}
