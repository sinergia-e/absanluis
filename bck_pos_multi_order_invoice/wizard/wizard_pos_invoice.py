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
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WizardMassInvoice(models.TransientModel):
    _name = 'wizard.mass.invoice'
    _description = 'Mass Invoice Wizard'

    def _default_pos_orders(self):
        return [(6, 0, self.env.context.get('active_ids', []))]

    def _default_edi_payment_method(self):
        l10n_mx_edi_payment_method_id = False

        domain = [
            ('pos_order_id', 'in', self.env.context.get('active_ids', []))]
        pos_payments = self.env['pos.payment'].read_group(
            domain, fields=['payment_method_id', 'amount:sum'],
            groupby=['payment_method_id'], limit=1, orderby='amount DESC', lazy=False)
        if pos_payments:
            l10n_mx_edi_payment_method_id = self.env['pos.payment.method'].browse(
                pos_payments[0]['payment_method_id'][0]).l10n_mx_edi_payment_method_id

        return l10n_mx_edi_payment_method_id

    def _default_journal_id(self):
        journal_id = False

        pos_order_ids = self.env['pos.order'].browse(self.env.context.get('active_ids', []))
        config_id = {}
        for pos_order_id in pos_order_ids:
            if pos_order_id.session_id.config_id.id in config_id:
                config_id[pos_order_id.session_id.config_id.id] += 1
            else:
                config_id.update({pos_order_id.session_id.config_id.id: 1})
        pos_config_id = self.env['pos.config'].browse(sorted(config_id.items(), key=lambda x: x[1], reverse=True)[0][0])
        if pos_config_id and pos_config_id.journal_id:
            journal_id = pos_config_id.journal_id.id

        return journal_id

    @api.model
    def _get_default_currency(self):
        ''' Get the currency of the first pos order, the currency of all orders must be the same. '''
        if self.env.context.get('active_ids', []):
            return self.env['pos.order'].browse(self.env.context.get('active_ids', [])[0]).currency_id
        else:
            return self.env.user.company_id.currency_id

    customer_id = fields.Many2one('res.partner', string="Customer", required=True)

    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True,
        domain="[('type', 'in', ['sale', 'general'])]",
        default=_default_journal_id)

    l10n_mx_edi_usage = fields.Selection([
        ('G01', 'Acquisition of merchandise'),
        ('G02', 'Returns, discounts or bonuses'),
        ('G03', 'General expenses'),
        ('I01', 'Constructions'),
        ('I02', 'Office furniture and equipment investment'),
        ('I03', 'Transportation equipment'),
        ('I04', 'Computer equipment and accessories'),
        ('I05', 'Dices, dies, molds, matrices and tooling'),
        ('I06', 'Telephone communications'),
        ('I07', 'Satellite communications'),
        ('I08', 'Other machinery and equipment'),
        ('D01', 'Medical, dental and hospital expenses.'),
        ('D02', 'Medical expenses for disability'),
        ('D03', 'Funeral expenses'),
        ('D04', 'Donations'),
        ('D05', 'Real interest effectively paid for mortgage loans (room house)'),
        ('D06', 'Voluntary contributions to SAR'),
        ('D07', 'Medical insurance premiums'),
        ('D08', 'Mandatory School Transportation Expenses'),
        ('D09', 'Deposits in savings accounts, premiums based on pension plans.'),
        ('D10', 'Payments for educational services (Colegiatura)'),
        ('P01', 'To define'),
    ], 'Usage', default='P01',
        required=True,
        help='Used in CFDI 3.3 to express the key to the usage that will '
        'gives the receiver to this invoice. This value is defined by the '
        'customer. \nNote: It is not cause for cancellation if the key set is '
        'not the usage that will give the receiver of the document.')

    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        string='Payment Way',
        required=True,
        help='Indicates the way the invoice was/will be paid, where the '
        'options could be: Cash, Nominal Check, Credit Card, etc. Leave empty '
        'if unkown and the XML will show "Unidentified".',
        default=_default_edi_payment_method)

    pos_order_ids = fields.Many2many('pos.order', string="POS Orders", readonly=True, default=_default_pos_orders)

    currency_id = fields.Many2one(
        'res.currency', readonly=True, required=True,
        string='Currency',
        default=_get_default_currency)

    amount_total = fields.Monetary(
        string='Total', readonly=True,
        compute='_compute_amount')
    l10n_mx_edi_is_global_invoice = fields.Boolean(
            string='Is global invoice?', default=False, help="")

    @api.onchange('l10n_mx_edi_is_global_invoice')
    def set_general_public_partner(self):
        if self.l10n_mx_edi_is_global_invoice:
            res_partner_general_public = self.env.ref('bck_pos_multi_order_invoice.res_partner_general_public')
            self.customer_id = res_partner_general_public

    @api.onchange('customer_id')
    def get_10n_mx_edi_defaults(self):
        if self.customer_id:
            if self.customer_id.commercial_partner_id.l10n_mx_edi_usage:
                self.l10n_mx_edi_usage = self.customer_id.commercial_partner_id.l10n_mx_edi_usage
            # Comentar esto por el tema de la localización Mexicana, método: _default_edi_payment_method
            # if self.customer_id.l10n_mx_edi_payment_method_id:
            #    self.l10n_mx_edi_payment_method_id = self.customer_id.l10n_mx_edi_payment_method_id

    @api.depends('pos_order_ids')
    def _compute_amount(self):
        amount_total = 0
        for pos_order in self.pos_order_ids:
            amount_total += pos_order.amount_total
        self.amount_total = amount_total

    def create_invoice(self):
        pos_invoice_type = self.env.company.pos_invoice_type

        invoice_ids = []
        if pos_invoice_type == 'single':
            for pos_order_id in self.pos_order_ids:
                invoice_id = pos_order_id.action_pos_order_invoice()
                invoice_ids.append(invoice_id['res_id'])
        elif pos_invoice_type == 'mass':
            pos_orders = self.pos_order_ids

            # POS Orders validations
            if pos_orders:
                invoice_type = 'out_invoice' if pos_orders[0].amount_total >= 0 else 'out_refund'
                session_state = 'closed' if pos_orders[0].session_state == 'closed' else 'opened'
                currency_id = pos_orders[0].currency_id

            for pos_order in pos_orders:
                # Los pedidos deben ser todos ventas o todos REEMBOLSOS
                if pos_order.amount_total >= 0 and invoice_type == 'out_refund':
                    raise ValidationError(_("The type of all POS orders selected must be the same (sale or refund)."))
                elif pos_order.amount_total < 0 and invoice_type == 'out_invoice':
                    raise ValidationError(_("The type of all POS orders selected must be the same (sale or refund)."))

                # Los pedidos deben estar en sesión 'closed' or 'any' pero no mezladas
                if pos_order.closed_or_opened(pos_order.session_state) != session_state:
                    raise ValidationError(_("The session state of all POS orders selected must be the same, "
                                            "all closed or all opened."))

                # Si la sesión está abierta, veridicar que ningún producto sea NO facturable
                if session_state == 'opened':
                    for line in pos_order.lines:
                        if not line.product_id.product_tmpl_id.pos_global_invoice:
                            raise ValidationError(_(
                                "The session state must be closed, becouse at least one "
                                "product of the pos orders is not billable."))

                # Los pedidos deben estar en estado 'paid' or 'done'
                if pos_order.state not in ('paid', 'done'):
                    raise ValidationError(_("The state of all POS orders selected must be paid or done."))

                # Los pedidos deben tener la misma moneda
                if pos_order.currency_id != currency_id:
                    raise ValidationError(_("The currency of all POS orders selected must be the same."))

            if invoice_type == 'out_invoice':
                form_name = 'Customer Invoice'
            else:
                form_name = 'Customer Refund'

            invoice_ids = self.pos_order_ids.create_invoice_from_pos_orders(
                self.customer_id, self.journal_id, self.currency_id, self.l10n_mx_edi_usage,
                self.l10n_mx_edi_payment_method_id, self.l10n_mx_edi_is_global_invoice)

        return {
            'name': _(form_name),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'type': '" + invoice_type + "'}",
            'type': 'ir.actions.act_window',
            # 'nodestroy': True,
            'target': 'current',
            'res_id': invoice_ids.id or False,
        }


# Comentar esta función, ya que a veces se necesita cancelar una factura para que timbre correctamente
"""
class AccountInvoice(models.Model):
    _inherit = 'account.move'

    @api.multi
    def action_invoice_cancel(self):
        res = super(AccountInvoice, self).action_invoice_cancel()
        pos_invoice_type = self.env['ir.config_parameter'].sudo().get_param(
            'bck_pos_multi_order_invoice.pos_invoice_type')
        if pos_invoice_type == 'single':
            get_pos = self.env['pos.order'].search([('name', '=', self.origin)])
            get_pos.state = 'paid'
            get_pos.invoice_id = False
        elif pos_invoice_type == 'mass':
            if self.origin:
                pos_orders = self.origin.split(',')
                for pos_order in pos_orders:
                    get_pos = self.env['pos.order'].search([('name', '=', pos_order)])
                    for validate in get_pos:
                        validate.state = 'paid'
                        validate.invoice_id = False
            return res
"""
