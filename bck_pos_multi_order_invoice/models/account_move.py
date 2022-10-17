# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('partner_id')
    def _compute_sign_required(self):
        """Assign the "Sign CFDI?" value how in the partner"""
        out_invoice = self.filtered(lambda i: i.move_type == 'out_invoice')
        for record in out_invoice:
            record.l10n_mx_edi_sign_required = record.partner_id.commercial_partner_id.l10n_mx_edi_sign_required
            record.l10n_mx_edi_payment_sign_required = record.partner_id.commercial_partner_id.l10n_mx_edi_sign_required

        for record in self - out_invoice:
            record.l10n_mx_edi_sign_required = True
            record.l10n_mx_edi_payment_sign_required = True

    def _inverse_sign_required(self):
        return False

    is_multi_pos_order_invoice = fields.Boolean(default=False, readonly=True)
    l10n_mx_edi_sign_required = fields.Boolean(
        string='Sign CFDI?',
        compute='_compute_sign_required',
        default=True,
        store=True,
        inverse='_inverse_sign_required',
        states={'draft': [('readonly', False)]},
        help='If this field is active, the CFDI will be generated for this invoice.')

    l10n_mx_edi_payment_sign_required = fields.Boolean(
        string='Sign CFDI Payment?',
        compute='_compute_sign_required',
        default=True,
        store=True,
        inverse='_inverse_sign_required',
        states={'draft': [('readonly', False)]},
        help='If this field is active, the CFDI payment will be generated for this invoice payments.')

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()

        for invoice in self:
            for pos_order in invoice.pos_order_ids:
                pos_order.state = 'done'
                pos_order.account_move = False
        return res

    def l10n_mx_edi_is_required(self):
        self.ensure_one()

        return (self.l10n_mx_edi_sign_required and super(AccountMove, self).l10n_mx_edi_is_required())

    """ TODO: Revisar si es la solución para no crear los asientos contables de costo y de salida de mercancía
    def is_sale_document(self, include_receipts=False):
        if self.is_multi_pos_order_invoice == True:
            return False
        else:
            return self.move_type in self.get_sale_types(include_receipts)
    """

    # Override this method
    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        ''' Prepare values used to create the journal items (account.move.line) corresponding to the Cost of Good Sold
        lines (COGS) for customer invoices.

        Example:

        Buy a product having a cost of 9 being a storable product and having a perpetual valuation in FIFO.
        Sell this product at a price of 10. The customer invoice's journal entries looks like:

        Account                                     | Debit | Credit
        ---------------------------------------------------------------
        200000 Product Sales                        |       | 10.0
        ---------------------------------------------------------------
        101200 Account Receivable                   | 10.0  |
        ---------------------------------------------------------------

        This method computes values used to make two additional journal items:

        ---------------------------------------------------------------
        220000 Expenses                             | 9.0   |
        ---------------------------------------------------------------
        101130 Stock Interim Account (Delivered)    |       | 9.0
        ---------------------------------------------------------------

        Note: COGS are only generated for customer invoices except refund made to cancel an invoice.

        :return: A list of Python dictionary to be passed to env['account.move.line'].create.
        '''
        lines_vals_list = []
        for move in self:
            # Make the loop multi-company safe when accessing models like product.product
            move = move.with_company(move.company_id)

            if not move.is_sale_document(include_receipts=True) or \
               not move.company_id.anglo_saxon_accounting or self.is_multi_pos_order_invoice:
                continue

            for line in move.invoice_line_ids:

                # Filter out lines being not eligible for COGS.
                if not line._eligible_for_cogs():
                    continue

                # Retrieve accounts needed to generate the COGS.
                accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=move.fiscal_position_id)
                debit_interim_account = accounts['stock_output']
                credit_expense_account = accounts['expense'] or move.journal_id.default_account_id
                if not debit_interim_account or not credit_expense_account:
                    continue

                # Compute accounting fields.
                sign = -1 if move.move_type == 'out_refund' else 1
                price_unit = line._stock_account_get_anglo_saxon_price_unit()
                balance = sign * line.quantity * price_unit

                # Add interim account line.
                lines_vals_list.append({
                    'name': line.name[:64],
                    'move_id': move.id,
                    'partner_id': move.commercial_partner_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': price_unit,
                    'debit': balance < 0.0 and -balance or 0.0,
                    'credit': balance > 0.0 and balance or 0.0,
                    'account_id': debit_interim_account.id,
                    'exclude_from_invoice_tab': True,
                    'is_anglo_saxon_line': True,
                })

                # Add expense account line.
                lines_vals_list.append({
                    'name': line.name[:64],
                    'move_id': move.id,
                    'partner_id': move.commercial_partner_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': -price_unit,
                    'debit': balance > 0.0 and balance or 0.0,
                    'credit': balance < 0.0 and -balance or 0.0,
                    'account_id': credit_expense_account.id,
                    'analytic_account_id': line.analytic_account_id.id,
                    'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'exclude_from_invoice_tab': True,
                    'is_anglo_saxon_line': True,
                })
        return lines_vals_list


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_mx_edi_identification_number = fields.Char(
        string='Identification #',
        help="In this field, the folio or transaction number of the transaction vouchers with "
        "the general public must be recorded.")
