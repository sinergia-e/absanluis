# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY Odoo S.A. <http://www.odoo.com>
#    @author Paramjit Singh A. Sahota <sahotaparamjitsingh@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _is_required_for_invoice(self, invoice):
        # OVERRIDE
        self.ensure_one()
        if self.code != 'cfdi_3_3' and invoice.l10n_mx_edi_sign_required is True:
            return super()._is_required_for_invoice(invoice)

        # Determine on which invoices the Mexican CFDI must be generated.
        return invoice.move_type in ('out_invoice', 'out_refund') and invoice.country_code == 'MX' \
            and invoice.l10n_mx_edi_sign_required

    def _is_required_for_payment(self, move):
        # OVERRIDE
        self.ensure_one()

        sign_not_required = (
            move.payment_id.reconciled_invoice_ids.filtered(lambda i: i.l10n_mx_edi_payment_sign_required is False))

        if self.code != 'cfdi_3_3' and sign_not_required is False:
            return super()._is_required_for_payment(move)

        # Determine on which invoices the Mexican CFDI must be generated.
        if move.country_code != 'MX' or sign_not_required:
            return False

        if (move.payment_id or move.statement_line_id).l10n_mx_edi_force_generate_cfdi:
            return True

        reconciled_invoices = move._get_reconciled_invoices()
        return 'PPD' in reconciled_invoices.mapped('l10n_mx_edi_payment_policy')
