from odoo import models, fields, api
from datetime import datetime, timedelta, date


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    def _send_license_expiration_notification(self):
        today = fields.Date.today()
        one_month_from_now = today + timedelta(days=30)

        # Search for vehicles with expiration date within one month
        vehicles_expiring = self.search([
            ('license_expiry_date', '<=', one_month_from_now),
            ('license_expiry_date', '>=', today)
        ])
        print("???????????????????????????????????????????????????????????????????????")
        for license in vehicles_expiring:
            # Prepare message content
            message_body = f"Driver {license.name} (License No: {license.license_number}) will expire on {license.license_expiry_date}. Please renew the license."
            user = self.env.ref('base.user_admin')  # Admin user
            # Send an internal note to the responsible user (e.g., fleet manager)
            license.message_post(
                body=message_body,
                subject="Vehicle License Expiration Reminder",
                message_type='notification',
                subtype_id=self.env.ref('mail.mt_note').id,
                partner_ids=[self.env.user.partner_id.id]
            )
            # Create an activity for the user
            activity_type = self.env.ref('mail.mail_activity_data_todo')  # To Do activity
            self.env['mail.activity'].create({
                'res_model_id': self.env['ir.model']._get('hr.employee').id,
                'res_id': license.id,
                'activity_type_id': activity_type.id,
                'summary': 'License Expiration Reminder',
                'note': f"The license of Driver {license.name} will expire on {license.license_expiry_date}.",
                'date_deadline': license.license_expiry_date,
                'user_id': user.id,
            })

