# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _create_invoice(self):
        """
        This method creates an invoice for the POS order.
        """
        # Define account move (invoice) model
        AccountMove = self.env['account.move']
        invoice_ids = []

        for order in self:
            if not order.partner_id:
                raise ValueError("You must assign a customer to create an invoice.")

            # Prepare invoice data
            move_vals = {
                'move_type': 'out_invoice',
                'partner_id': order.partner_id.id,
                'invoice_origin': order.name,
                'invoice_date': fields.Date.context_today(self),
                'invoice_line_ids': [],
            }

            # Prepare invoice lines from POS order lines
            invoice_lines = []
            for line in order.lines:
                # Prepare invoice line data
                invoice_line_vals = {
                    'name': line.product_id.display_name,
                    'quantity': line.qty,
                    'price_unit': line.price_unit,
                    'product_id': line.product_id.id,
                    'tax_ids': [(6, 0, line.tax_ids_after_fiscal_position.ids)],
                    'account_id': line.product_id.categ_id.property_account_income_categ_id.id,
                }
                invoice_lines.append((0, 0, invoice_line_vals))

            move_vals['invoice_line_ids'] = invoice_lines

            # Create the invoice (account.move record)
            invoice = AccountMove.create(move_vals)
            invoice_ids.append(invoice.id)

            # Post the invoice (if you want to automatically validate it)
            invoice.action_post()

        return invoice_ids

    def action_pos_order_paid(self):
        """
        Override the POS order 'paid' action to trigger invoice creation.
        """
        res = super(PosOrder, self).action_pos_order_paid()
        self._create_invoice()  # Automatically create an invoice when the order is paid
        return res
