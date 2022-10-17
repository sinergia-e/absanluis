# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#################################################################################
# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_invoice_type = fields.Selection(
        string='Invoice Type',
        related='company_id.pos_invoice_type',
        readonly=False,
        help="If marked, restrict Sale Order confirmation if the customer has exeeded the credit limit.")

    create_out_refund_as_payment = fields.Boolean(
        string='Create credit note as payment',
        related='company_id.create_out_refund_as_payment',
        readonly=False,
        help="If marked, the multi pos order invoice will be paid with a new credit note.")
