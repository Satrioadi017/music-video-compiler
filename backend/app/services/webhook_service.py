import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WebhookService:
    async def send_webhook(self, webhook, event: str, data: dict) -> dict:
        payload = {
            "event": event,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "webhook_id": str(webhook.id),
        }

        headers = {"Content-Type": "application/json", **webhook.headers}

        if webhook.secret:
            signature = hmac.new(
                webhook.secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(webhook.url, json=payload, headers=headers)
                webhook.last_triggered_at = datetime.now(timezone.utc)
                webhook.last_response_status = response.status_code
                if response.status_code >= 400:
                    webhook.failure_count += 1
                    webhook.last_error = response.text[:500]
                else:
                    webhook.failure_count = 0
                    webhook.last_error = None

                return {
                    "status_code": response.status_code,
                    "body": response.text[:500],
                }
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            webhook.failure_count += 1
            webhook.last_error = str(e)[:500]
            return {"status_code": 0, "body": str(e)}

    async def trigger_event(self, db, user_id, event: str, data: dict):
        from sqlalchemy import select
        from app.models.webhook import Webhook

        result = await db.execute(
            select(Webhook).where(
                Webhook.user_id == user_id,
                Webhook.is_active.is_(True),
            )
        )
        webhooks = result.scalars().all()

        for webhook in webhooks:
            if event in webhook.events or not webhook.events:
                await self.send_webhook(webhook, event, data)
