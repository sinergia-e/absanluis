# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class SaleFrequentSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    days = fields.Integer(string='Dias(s)')

    def set_values(self):
        res = super(SaleFrequentSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('product_sales_price_update_report.days', self.days)
        return res

    @api.model
    def get_values(self):
        res = super(SaleFrequentSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        days = float(ICPSudo.get_param('product_sales_price_update_report.days')) or 1

        res.update(
            days=days,
        )
        return res
