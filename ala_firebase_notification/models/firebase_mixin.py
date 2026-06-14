import os
import json

from odoo import models
from odoo.tools import config
from odoo.exceptions import UserError

from google.oauth2 import service_account
from google.auth.transport.requests import Request


class AlaFirebaseMixin(models.AbstractModel):
    _name = "ala.firebase.mixin"
    _description = "ALA Firebase Helper"

    def _get_firebase_service_account_path(self):
        service_account_path = config.get("firebase_service_account")

        if not service_account_path:
            raise UserError(
                "Firebase service account is not configured in odoo.conf"
            )

        if not os.path.isfile(service_account_path):
            raise UserError(
                "Firebase service account file not found: %s"
                % service_account_path
            )

        return service_account_path

    def _get_firebase_project_id(self):
        service_account_path = self._get_firebase_service_account_path()

        with open(service_account_path, "r") as f:
            service_data = json.load(f)

        project_id = service_data.get("project_id")

        if not project_id:
            raise UserError(
                "project_id not found in Firebase service account file"
            )

        return project_id

    def _get_firebase_access_token(self):
        service_account_path = self._get_firebase_service_account_path()

        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=[
                "https://www.googleapis.com/auth/firebase.messaging"
            ]
        )

        credentials.refresh(Request())

        return credentials.token