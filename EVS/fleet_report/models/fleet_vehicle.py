from odoo import models, fields, api
from datetime import datetime, timedelta, date


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    end_license_date = fields.Date(tracking=True, string="End Date")
    notification_date = fields.Date(string="Notification Date", compute="_compute_notification_date", store=True)

    def _send_license_expiration_notification(self):
        today = fields.Date.today()
        one_month_from_now = today + timedelta(days=30)

        # Search for vehicles with expiration date within one month
        vehicles_expiring = self.search([
            ('end_license_date', '<=', one_month_from_now),
            ('end_license_date', '>=', today)
        ])
        print("???????????????????????????????????????????????????????????????????????")
        for vehicle in vehicles_expiring:
            # Prepare message content
            message_body = f"Vehicle {vehicle.name} (License No: {vehicle.license_number}) will expire on {vehicle.end_license_date}. Please renew the license."
            user = self.env.ref('base.user_admin')  # Admin user
            # Send an internal note to the responsible user (e.g., fleet manager)
            vehicle.message_post(
                body=message_body,
                subject="Vehicle License Expiration Reminder",
                message_type='notification',
                subtype_id=self.env.ref('mail.mt_note').id,
                partner_ids=[self.env.user.partner_id.id]
            )

            # Create an activity for the user
            activity_type = self.env.ref('mail.mail_activity_data_todo')  # To Do activity
            self.env['mail.activity'].create({
                'res_model_id': self.env['ir.model']._get('fleet.vehicle').id,
                'res_id': vehicle.id,
                'activity_type_id': activity_type.id,
                'summary': 'License Expiration Reminder',
                'note': f"The license of vehicle {vehicle.name} will expire on {vehicle.end_license_date}.",
                'date_deadline': vehicle.end_license_date,
                'user_id': user.id,
            })
