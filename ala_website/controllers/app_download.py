from odoo import http
from odoo.http import request
import os

class ApkDownloadController(http.Controller):

    @http.route('/download/mis-app', type='http', auth='public', website=True)
    def download_apk(self):
        # Absolute path to APK
        apk_path = os.path.join(
            os.path.dirname(__file__),
            '..', 'static', 'apk', 'MIS_School_App.apk'
        )
        print('AAAAAAAAAAAAAAAAAAA=================',apk_path)

        return http.send_file(
            apk_path,
            mimetype='application/vnd.android.package-archive',
            as_attachment=True,
            filename='MIS_School_App.apk'
        )
