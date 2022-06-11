# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class CerateInvoiceWizard(models.TransientModel):

    _name = 'create.invoice.wizard'
    
#    invoice_format = fields.Selection(selection=[('detailed', 'Detallada'), ('one', 'Una partida'), ('cfdi', 'CFDI'), ('compacta','Compacta')], string='Facturar en forma', required=True, default='detailed')
    invoice_format = fields.Selection(selection=[('detailed', 'Detallada'), ('compacta','Compacta')], string='Como quieres la factura', required=True, default='detailed')
    partner_id = fields.Many2one('res.partner', string=_('Cliente'))
    product_id = fields.Many2one('product.product', string=_('Artículo general'))
    order_num = fields.Integer(string=_('No. de pedidos'), readonly=True)
    total = fields.Float(string=_('Total'), readonly=True)

    @api.model
    def default_get(self, fields):
        data = super(CerateInvoiceWizard, self).default_get(fields)
        order_is = self._context.get('active_ids')
        orders = self.env['pos.order'].browse(order_is)
        data['order_num'] = len(order_is)
        data['total'] = sum(o.amount_total for o in orders)
        return data
 
    
    def action_create_invoices(self):
        order_is = self._context.get('active_ids')
        orders = self.env['pos.order'].browse(order_is)
        posted_order = orders.search([('state','=','done')])
        if posted_order:
            if self.invoice_format in ['one', 'cfdi']:
                orders.action_factura_global_total(product_total=self.product_id, partner_total=self.partner_id, invoice_format=self.invoice_format)
            elif self.invoice_format == 'compacta':
                orders.action_factura_global_compacta(partner_total=self.partner_id)
            else:
                orders.action_factura_global(partner_total=self.partner_id)
        else:
            if self.invoice_format in ['one', 'cfdi']:
                orders.action_invoice_total(product_total=self.product_id, partner_total=self.partner_id, invoice_format=self.invoice_format)
            elif self.invoice_format == 'compacta':
                orders.action_invoice_compacta(partner_total=self.partner_id)
            else:
                orders.action_invoice(partner_total=self.partner_id)
        return True
