from odoo import models
from odoo.exceptions import UserError
from odoo.tools import config
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os


class AlaFirebaseMixin(models.AbstractModel):
    _name = "ala.firebase.mixin"
    _description = "ALA Firebase Helper"

    def _get_firebase_access_token(self):
        service_account_path = config.get("firebase_service_account")

        if not service_account_path:
            raise UserError(
                "Firebase service account is not configured in odoo.conf"
            )

        if not os.path.isfile(service_account_path):
            raise UserError(
                f"Firebase service account file not found: {service_account_path}"
            )

        scopes = [
            "https://www.googleapis.com/auth/firebase.messaging"
        ]

        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=scopes
        )

        credentials.refresh(Request())
        return credentials.token
