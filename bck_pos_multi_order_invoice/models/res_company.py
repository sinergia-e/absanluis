# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    pos_invoice_type = fields.Selection(
        [('single', 'Single'), ('mass', 'Mass')],
        string='Invoice Type',
        default='mass',
        help="Select \"Mass\" for create one invoice of several POS orders, select \"Single\" for create one invoice for each POS order.")

    create_out_refund_as_payment = fields.Boolean(
        string='Create credit note as payment',
        default=True,
        help="If marked, the multi pos order invoice will be paid with a new credit note.")
