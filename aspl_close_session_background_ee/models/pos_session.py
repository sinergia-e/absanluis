# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    is_close_session_background = fields.Boolean(string="Cierra Sesion")

    def action_close_session_background(self):
        self.is_close_session_background = True

    def action_stop_session_background(self):
        self.is_close_session_background = False

    @api.model
    def inform_close_session(self):
        pos_session = self.env['pos.session'].search([('is_close_session_background', '=', True),
                                                      '|', ('state', '=', 'closing_control'), ('state', '=', 'opened')])
        for each_session in pos_session:
            try:
                if not each_session.config_id.cash_control:
                    each_session.action_pos_session_closing_control()
                else:
                    if each_session.cash_register_balance_end_real == 0.00:
                        if each_session.cash_register_balance_end > 0.00:
                            for statement in each_session.statement_ids:
                                statement.write({'balance_end_real': statement.balance_end})
                    each_session.action_pos_session_close()

                body = """
                        <p>Hello,%s</p>
                        <p>Session %s is successfully closed.</p>""" % (each_session.user_id.name, each_session.name)
                values = {
                    'subject': 'Successfully close the session - ' + each_session.name,
                    'body_html': body,
                    'email_to': each_session.user_id.partner_id.email,
                    'email_from': each_session.user_id.partner_id.email,
                    'message_type': 'email',
                    'author_id': each_session.user_id.partner_id.id
                }
                mail_id = self.env['mail.mail'].sudo().create(values)
                try:
                    mail_id.send()
                    if not each_session.stop_at:
                        each_session.write({'stop_at': fields.Datetime.now()})
                except:
                    pass

            except Exception as e:
                _logger.error(e)

                body = """
                        <p>Hello,%s</p>
                        <p>Session : %s</p>
                        <p>Reason : %s</p>""" % (each_session.user_id.name, each_session.name, e.args[0])
                values = {
                    'subject': 'Error al cerrar sesion- ' + each_session.name,
                    'body_html': body,
                    'email_to': each_session.user_id.partner_id.email,
                    'email_from': each_session.user_id.partner_id.email,
                    'message_type': 'email',
                    'author_id': each_session.user_id.partner_id.id
                }
                mail_id = self.env['mail.mail'].sudo().create(values)
                try:
                    mail_id.send()
                except:
                    pass

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
