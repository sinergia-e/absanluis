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


class CloseAllSession(models.Model):
    _name = 'wizard.all.session.close'
    _description = "All Session Close Wizard"

    all_session_close = fields.Boolean(string="All In Progress Session Close in background")

    def pos_all_session_close(self):
        if self.all_session_close:
            pos_session = self.env['pos.session'].search(
                ['|', ('state', '=', 'closing_control'), ('state', '=', 'opened')])

            for each_session in pos_session:
                each_session.is_close_session_background = True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
