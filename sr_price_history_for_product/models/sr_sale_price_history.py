# -*- coding: utf-8 -*-
##############################################################################
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class srSalePriceHistory(models.Model):
    _name = 'sr.sale.price.history'
    _description = 'Sale Price History'

    name = fields.Many2one("sale.order.line",string="Linea de orden de venta")  
    partner_id = fields.Many2one("res.partner",string="Cliente")
    user_id = fields.Many2one("res.users",string="Vendedor")
    product_tmpl_id = fields.Many2one("product.template",string="Template Id")
    variant_id = fields.Many2one("product.product",string="Producto")
    sale_order_id = fields.Many2one("sale.order",string="Orden de venta")
    sale_order_date = fields.Datetime(string="Fecha de la orden")
    product_uom_qty = fields.Float(string="Cantidad")
    unit_price = fields.Float(string="Precio")
    currency_id = fields.Many2one("res.currency",string="Moneda")
    total_price = fields.Monetary(string="Total")


