# -*- coding: utf-8 -*-


from odoo import fields, models,tools,api, _
from functools import partial


class sale_order(models.Model):
    _inherit = 'sale.order'

    pos_reference = fields.Char(string='Receipt Ref', readonly=True, copy=False)

    def _order_line_fields(self, line):
        line2 = [0,0,{}]
        if line and 'tax_ids' not in line[2]:
            product = self.env['product.product'].browse(line[2]['product_id'])
            line2[2]['tax_id'] = [(6, 0, [x.id for x in product.taxes_id])]
        line2[2]['product_id'] = line[2]['product_id']
        line2[2]['product_uom_qty'] = line[2]['qty']
        line2[2]['price_unit'] = line[2]['price_unit']
        line2[2]['discount'] = line[2]['discount']
        line2[2]['price_subtotal'] = line[2]['price_subtotal']
        return line2

    @api.model
    def _order_fields(self, ui_order):
        process_line = partial(self._order_line_fields)
        return {
            'user_id':  ui_order['user_id'],
            'order_line':   [process_line(l) for l in ui_order['lines']] if ui_order['lines'] else False,
            'partner_id':   ui_order['partner_id'] or False,
            'fiscal_position_id': ui_order['fiscal_position_id'],
            'note':         ui_order['wv_note'],
            'pos_reference': ui_order['name'],
        }
    @api.model
    def create_new_quotation(self,orders):
        submitted_references = [o['data']['name'] for o in orders]
        pos_order = self.search([('pos_reference', 'in', submitted_references)])
        existing_orders = pos_order.read(['pos_reference'])
        existing_references = set([o['pos_reference'] for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']['name'] not in existing_references]
        order_ids = []
        for quot in orders_to_save:
            quotation_obj = self.create(self._order_fields(quot['data']))
            session_id = self.env['pos.session'].browse(quot['data']['pos_session_id'])
            if session_id.config_id.picking_type_id:
                quotation_obj.warehouse_id = session_id.config_id.picking_type_id.warehouse_id.id
            if session_id.config_id.pos_sale_order_state == 'sale_order':
                quotation_obj.action_confirm()
            order_ids.append(quotation_obj.id)
            # order_line = self.env['pos.quotation.line'].search_read([('quotation_id','=',quotation_obj.id)],[])
        return order_ids

class pos_config(models.Model):
    _inherit = 'pos.config' 
    
    allow_create_sale_order = fields.Boolean("Create Sale Order")
    pos_sale_order_state = fields.Selection([('draft', 'Quotation'), ('sale_order', 'Confirm')],'State', default='draft')