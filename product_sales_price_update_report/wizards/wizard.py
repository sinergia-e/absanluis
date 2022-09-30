# -*- coding: utf-8 -*-
import datetime

import pytz

from odoo import fields, models, api


class PriceUpdateDetails(models.AbstractModel):
    _name = 'report.product.sales.price.update'

    def _get_report_values(self, docids, data=None):
        return data


class DatesSelect(models.TransientModel):
    _name = "date.select.wizard"

    from_date = fields.Date('From')
    to_date = fields.Date('To')

    def print_report(self):
        all_updated_products = []
        lst_price_field_id = self.env["ir.model.fields"].search(
            [("name", "=", "lst_price"), ("model", "in", ["product.product", "product.template"])])
        transactions = self.env['mail.tracking.value'].sudo().search(
            [('field', 'in', lst_price_field_id.ids), ('create_date', '>=', self.from_date),
             ('create_date', '<=', self.to_date)])

        user_time_zone = pytz.timezone(self.env.user.partner_id.tz)
        for transaction in transactions:
            user_time = pytz.utc.localize(transaction.create_date, is_dst=False)
            updated_on = user_time.astimezone(user_time_zone)
            d = {'product_name': self.env[transaction.mail_message_id.model].browse(
                transaction.mail_message_id.res_id).name,
                 'old_sale_price': transaction.old_value_float,
                 'new_sale_price': transaction.new_value_float,
                 'price_updated_on': updated_on,
                 'price_updated_by': self.env['res.users'].browse(int(transaction.create_uid)).name
                 }
            all_updated_products.append(d)
        return self.env.ref('product_sales_price_update_report.sales_price_update_report_action').report_action([],
                                                                                                                data={
                                                                                                                    'products': all_updated_products})

    def send_report(self):
        for rec in self:
            template_id = self.env.ref('product_sales_price_update_report.email_template_sales_price_update_report').id
            template = self.env['mail.template'].browse(template_id)
            template.browse(template_id).send_mail(rec.id, force_send=True)

    @api.model
    def send_auto_report(self):
        rec = self.sudo().create({})
        template_id = self.env.ref('product_sales_price_update_report.email_template_sales_price_update_report').id
        template = self.env['mail.template'].browse(template_id)
        template.browse(template_id).send_mail(rec.id, force_send=True)

    def get_details(self):
        if self.from_date and self.to_date:
            from_date = self.from_date
            to_date = self.to_date
        else:
            ICPSudo = self.env['ir.config_parameter'].sudo()
            days = int(ICPSudo.get_param('product_sales_price_update_report.days'))
            to_date = datetime.date.today()
            from_date = datetime.date.today() - datetime.timedelta(days=days)
        all_updated_products = []
        # transactions = self.env['mail.tracking.value'].sudo().search(
        #     [('field', '=', 'lst_price'), ('create_date', '>=', from_date),
        #      ('create_date', '<=', to_date)])

        lst_price_field_id = self.env["ir.model.fields"].search(
            [("name", "=", "lst_price"), ("model", "in", ["product.product", "product.template"])])
        transactions = self.env['mail.tracking.value'].sudo().search(
            [('field', 'in', lst_price_field_id.ids), ('create_date', '>=', from_date),
             ('create_date', '<=', to_date)])

        user_time_zone = pytz.timezone(self.env.user.partner_id.tz)
        for transaction in transactions:
            user_time = pytz.utc.localize(transaction.create_date, is_dst=False)
            updated_on = user_time.astimezone(user_time_zone)
            d = {'product_name': self.env[transaction.mail_message_id.model].browse(
                transaction.mail_message_id.res_id).name,
                 'old_sale_price': transaction.old_value_float,
                 'new_sale_price': transaction.new_value_float,
                 'price_updated_on': updated_on,
                 'price_updated_by': self.env['res.users'].browse(int(transaction.create_uid)).name
                 }
            all_updated_products.append(d)
        return all_updated_products

    # def action_get_attachment(self):
    #     """ this method called from button action in view xml """
    #     pdf = self.env.ref('module_name..report_id').render_qweb_pdf(self.ids)
    #     b64_pdf = base64.b64encode(pdf[0])
    #     # save pdf as attachment
    #     name = "My Attachment"
    #     return self.env['ir.attachment'].create({
    #         'name': name,
    #         'type': 'binary',
    #         'datas': b64_pdf,
    #         'datas_fname': name + '.pdf',
    #         'store_fname': name,
    #         'res_model': self._name,
    #         'res_id': self.id,
    #         'mimetype': 'application/x-pdf'
    #     })
