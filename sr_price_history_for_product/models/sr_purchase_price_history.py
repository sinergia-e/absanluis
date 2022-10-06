# -*- coding: utf-8 -*-
##############################################################################
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class srPurchasePriceHistory(models.Model):
    _name = 'sr.purchase.price.history'
    _description = 'Purchase Price History'

    name = fields.Many2one("purchase.order.line",string="Linea de la orden de compra")  
    partner_id = fields.Many2one("res.partner",string="Proveedor ABSL")
    user_id = fields.Many2one("res.users",string="Encargado")
    product_tmpl_id = fields.Many2one("product.template",string="Template Id")
    variant_id = fields.Many2one("product.product",string="Producto")
    purchase_order_id = fields.Many2one("purchase.order",string="Orden de compra")
    purchase_order_date = fields.Datetime(string="Fecha de la compra")
    product_uom_qty = fields.Float(string="Cantidad")
    unit_price = fields.Float(string="Precio")
    currency_id = fields.Many2one("res.currency",string="Moneda")
    total_price = fields.Monetary(string="Total")

