# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    lst_price = fields.Float(
        'Sales Price', related='list_price', readonly=False, track_visibility='onchange',
        digits='Product Price')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    lst_price = fields.Float(
        'Public Price', compute='_compute_product_lst_price',
        digits='Product Price', inverse='_set_product_lst_price',
        help="The sale price is managed from the product template. Click on the 'Configure Variants' button to set the extra attribute prices.",
        track_visibility='onchange')
