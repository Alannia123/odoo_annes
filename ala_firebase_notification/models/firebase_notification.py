import requests
import json
from odoo import models
import logging
_logger = logging.getLogger(__name__)

class AlaFirebaseNotification(models.Model):
    _name = "ala.firebase.notification"
    _inherit = "ala.firebase.mixin"

    def send_android_notification(self, title, body, data=None):
        access_token = self._get_firebase_access_token()

        project_id = self._get_firebase_project_id()
        print('ACESSSS=================',access_token)

        url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"

        payload = {
            "message": {
                "topic": "all",
                "notification": {
                    "title": title,
                    "body": body,
                },
                "android": {
                    "priority": "high"
                }
            }
        }

        if data:
            payload["message"]["data"] = data

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,  # ✅ better than data=json.dumps
            timeout=20
        )

        _logger.info("FCM STATUS: %s", response.status_code)
        _logger.info("FCM RESPONSE: %s", response.text)

        return response.json()

