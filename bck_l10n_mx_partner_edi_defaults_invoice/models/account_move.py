# -*- coding: utf-8 -*-
from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        '''Set the payment l10n_mx_edi_usage on the sale order as the first of the selected partner.
        '''
        # OVERRIDE
        res = super(AccountMove, self)._onchange_partner_id()
        if self.partner_id:
            # EDI Usage from Partner
            if self.partner_id.commercial_partner_id.is_company and self.partner_id.commercial_partner_id.l10n_mx_edi_usage:
                self.l10n_mx_edi_usage = self.partner_id.commercial_partner_id.l10n_mx_edi_usage

            # Method from Partner
            if self.partner_id.commercial_partner_id.is_company and self.partner_id.commercial_partner_id.l10n_mx_edi_payment_method_id:
                self.l10n_mx_edi_payment_method_id = self.partner_id.commercial_partner_id.l10n_mx_edi_payment_method_id
        return res
