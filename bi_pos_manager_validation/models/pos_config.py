# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import html2plaintext
import odoo.addons.decimal_precision as dp

class ResUsers(models.Model):
    _inherit = 'res.users'

    pos_security_pin = fields.Char(string='PIN de supervisor', size=32, help='Que no es obvio para que sirve?')

    @api.constrains('pos_security_pin')
    def _check_pin(self):
        if self.pos_security_pin and not self.pos_security_pin.isdigit():
            raise UserError(_("Criatura el PIN solo puede tener numeros ... "))



class PosConfigInherit(models.Model):
	_inherit = 'pos.config'

	user_id = fields.Many2one('res.users',string='Supervisor')
	close_pos = fields.Boolean(string='Cerrar sesion ')
	order_delete = fields.Boolean(string='Eliminar orden')
	order_line_delete = fields.Boolean(string='Eliminar Partida')
	qty_detail = fields.Boolean(string='Modificar Cantidad')
	discount_app = fields.Boolean(string='Aplicar Descuentos')
	payment_perm = fields.Boolean(string='Realiza Pagos')
	price_change = fields.Boolean(string='Cambiar Precios')
	one_time_valid = fields.Boolean(string='Password de un solo uso')
