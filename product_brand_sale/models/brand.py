# -*- coding: utf-8 -*-
#############################################################################
#
#    Sinergia.
#
#############################################################################




from odoo import models, fields, api


class ProductBrand(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand', string='Proveedor ABSL')


class BrandProduct(models.Model):
    _name = 'product.brand'

    name = fields.Char(String="Nombre de Proveedor")
    brand_image = fields.Binary()
    member_ids = fields.One2many('product.template', 'brand_id')
    product_count = fields.Char(String='Productos del Proveedor', compute='get_count_products', store=True)

    @api.depends('member_ids')
    def get_count_products(self):
        self.product_count = len(self.member_ids)


class BrandPivot(models.Model):
    _inherit = 'sale.report'

    brand_id = fields.Many2one('product.brand', string='Proveedor ABSL')

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['brand_id'] = ", t.brand_id as brand_id"
        groupby += ', t.brand_id'
        return super(BrandPivot, self)._query(with_clause, fields, groupby, from_clause)
    
    
    
    
    
    
    
    
    
    

    
    
    
# Codigo Adicional para stock
class BrandReportStock(models.Model):
    _inherit = 'stock.quant'
    brand_id = fields.Many2one(related='product_id.brand_id',
                               string='Proveedor ABSL', store=True, readonly=True)    
