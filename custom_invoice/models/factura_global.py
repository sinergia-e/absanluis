# -*- coding: utf-8 -*-
import base64
import datetime
import json

import pytz
import requests
from lxml import etree
from odoo import fields, api, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, Warning
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.lib.units import mm
import re

from . import amount_to_text_es_MX

class FacturaglobalLine(models.Model):
    _name = "factura.global.line"

    factura_global_id = fields.Many2one('factura.global', string="Factura Global")
    product_id = fields.Many2one('product.product', string='Product', required=True)
    name = fields.Text(string='Description', required=True, )
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                            default=1)
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    invoice_line_tax_ids = fields.Many2many('account.tax', string='Taxes')
    currency_id = fields.Many2one('res.currency', related='factura_global_id.currency_id', store=True,
                                  related_sudo=False, readonly=False)
    price_subtotal = fields.Monetary(string='Amount (without Taxes)',
                                     store=True, readonly=True, compute='_compute_price',
                                     help="Total amount without taxes")
    price_total = fields.Monetary(string='Amount (with Taxes)',
                                  store=True, readonly=True, compute='_compute_price', help="Total amount with taxes")
    discount = fields.Float(string='Descuento', digits=dp.get_precision('Product Price'))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        self.name = self.product_id.partner_ref
        company_id = self.env.user.company_id
        taxes = self.product_id.taxes_id.filtered(lambda r: r.company_id == company_id)
        self.invoice_line_tax_ids = fp_taxes = taxes
        fix_price = self.env['account.tax']._fix_tax_included_price
        self.price_unit = fix_price(self.product_id.lst_price, taxes, fp_taxes)

    @api.depends('price_unit', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'factura_global_id.partner_id', 'factura_global_id.currency_id', )
    def _compute_price(self):
        for line in self:
            currency = line.factura_global_id and line.factura_global_id.currency_id or None
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = False
            if line.invoice_line_tax_ids:
                taxes = line.invoice_line_tax_ids.compute_all(price, currency, line.quantity, product=line.product_id,
                                                              partner=line.factura_global_id.partner_id)
            line.price_subtotal = taxes['total_excluded'] if taxes else line.quantity * price
            line.price_total = taxes['total_included'] if taxes else line.price_subtotal

class Facturaglobal(models.Model):
    _name = "factura.global"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = "number"

    factura_cfdi = fields.Boolean('Factura CFDI')
    tipo_comprobante = fields.Selection(
        selection=[('I', 'Ingreso'),
                   ('E', 'Egreso'), ],
               #   ('T', 'Traslado'),
        string=_('Tipo de comprobante'), default='I'
    )
    number = fields.Char(string="Numero", store=True, readonly=True, copy=False,
                         default=lambda self: _('Draft Invoice'))
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('valid', 'Hecho'),
        ('cancel', 'Cancelado'),
    ], string='Status', index=True, readonly=True, default='draft', )

    forma_pago_id  =  fields.Many2one('catalogo.forma.pago', string='Forma de pago')
    
    methodo_pago = fields.Selection(
        selection=[('PUE', _('Pago en una sola exhibición')),
                   ('PPD', _('Pago en parcialidades o diferido')), ],
        string=_('Método de pago'), default='PUE'
    )

    uso_cfdi_id  = fields.Many2one('catalogo.uso.cfdi', string='Uso CFDI (cliente)') #, default = 'S01',)

    confirmacion = fields.Char(string=_('Confirmación'))
    estado_factura = fields.Selection(
        selection=[('factura_no_generada', 'Factura no generada'), ('factura_correcta', 'Factura correcta'),
                   ('solicitud_cancelar', 'Cancelación en proceso'), ('factura_cancelada', 'Factura cancelada'),
                   ('solicitud_rechazada', 'Cancelación rechazada'), ],
        string=_('Estado de factura'),
        default='factura_no_generada',
        readonly=True
    )
    fecha_factura = fields.Datetime(string=_('Fecha Factura'))
    tipo_relacion = fields.Selection(
        selection=[('01', 'Nota de crédito de los documentos relacionados'),
                   ('02', 'Nota de débito de los documentos relacionados'),
                   ('03', 'Devolución de mercancía sobre facturas o traslados previos'),
                   ('04', 'Sustitución de los CFDI previos'),
                   ('05', 'Traslados de mercancías facturados previamente'),
                   ('06', 'Factura generada por los traslados previos'),
                   ('07', 'CFDI por aplicación de anticipo')],
        string=_('Tipo relación')
    )

    uuid_relacionado = fields.Char(string=_('CFDI Relacionado'))
    qr_value = fields.Char(string=_('QR Code Value'))
    qrcode_image = fields.Binary("QRCode")
    comment = fields.Text("Comentario")
    partner_id = fields.Many2one('res.partner', string="Cliente", required=True, )
    source_document = fields.Char(string="Documento origen")
    invoice_date = fields.Datetime(string="Fecha de factura")
    factura_line_ids = fields.One2many('factura.global.line', 'factura_global_id', string='Factura global line',
                                       copy=True)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_compute_amount',
                                     currency_field='currency_id')
    amount_tax = fields.Monetary(string='Tax', store=True, readonly=True, compute='_compute_amount',
                                 currency_field='currency_id')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount',
                                   currency_field='currency_id')

    numero_cetificado = fields.Char(string=_('Numero de cetificado'))
    cetificaso_sat = fields.Char(string=_('Cetificao SAT'))
    folio_fiscal = fields.Char(string=_('Folio Fiscal'), readonly=True)
    fecha_certificacion = fields.Char(string=_('Fecha y Hora Certificación'))
    cadena_origenal = fields.Char(string=_('Cadena Origenal del Complemento digital de SAT'))
    selo_digital_cdfi = fields.Char(string=_('Selo Digital del CDFI'))
    selo_sat = fields.Char(string=_('Selo del SAT'))
    moneda = fields.Char(string=_('Moneda'))
    tipocambio = fields.Char(string=_('TipoCambio'))
    #folio = fields.Char(string=_('Folio'))
    #version = fields.Char(string=_('Version'))
    number_folio = fields.Char(string=_('Folio'), compute='_get_number_folio')
    amount_to_text = fields.Char('Amount to Text', compute='_get_amount_to_text',
                                 size=256, 
                                 help='Amount of the invoice in letter')
    qr_value = fields.Char(string=_('QR Code Value'))
    invoice_datetime = fields.Char(string=_('11/12/17 12:34:12'))
    proceso_timbrado = fields.Boolean(string=_('Proceso de timbrado'))
    rfc_emisor = fields.Char(string=_('RFC'))
    name_emisor = fields.Char(string=_('Name'))
    serie_emisor = fields.Char(string=_('A'))

    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Product Price'))
    monto = fields.Float(string='Amount', digits=dp.get_precision('Product Price'))
    precio_unitario = fields.Float(string='Precio unitario', digits=dp.get_precision('Product Price'))
    monto_impuesto = fields.Float(string='Monto impuesto', digits=dp.get_precision('Product Price'))
    total_impuesto = fields.Float(string='Monto impuesto', digits=dp.get_precision('Product Price'))
    decimales = fields.Float(string='decimales')
    desc = fields.Float(string='descuento', digits=dp.get_precision('Product Price'))
    subtotal = fields.Float(string='subtotal', digits=dp.get_precision('Product Price'))
    total = fields.Float(string='total', digits=dp.get_precision('Product Price'))
    company_id = fields.Many2one('res.company', 'Compañia',
                                 default=lambda self: self.env['res.company']._company_default_get('factura.global'))
    tax_payment = fields.Text(string=_('Taxes'))
    factura_global = fields.Boolean('Agregar factura global')
    fg_periodicidad = fields.Selection(
        selection=[('01', '01 - Diario'),
                   ('02', '02 - Semanal'),
                   ('03', '03 - Quincenal'),
                   ('04', '04 - Mensual'),
                   ('05', '05 - Bimestral'),],
        string=_('Periodicidad'),
    )
    fg_meses = fields.Selection(
        selection=[('01', '01 - Enero'),
                   ('02', '02 - Febrero'),
                   ('03', '03 - Marzo'),
                   ('04', '04 - Abril'),
                   ('05', '05 - Mayo'),
                   ('06', '06 - Junio'),
                   ('07', '07 - Julio'),
                   ('08', '08 - Agosto'),
                   ('09', '09 - Septiembre'),
                   ('10', '10 - Octubre'),
                   ('11', '11 - Noviembre'),
                   ('12', '12 - Diciembre'),
                   ('13', '13 - Enero - Febrero'),
                   ('14', '14 - Marzo - Abril'),
                   ('15', '15 - Mayo - Junio'),
                   ('16', '16 - Julio - Agosto'),
                   ('17', '17 - Septiembre - Octubre'),
                   ('18', '18 - Noviembre - Diciembre'),],
        string=_('Mes'),
    )
    fg_ano =  fields.Char(string=_('Año'))

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if self.estado_factura == 'factura_correcta' or self.estado_factura == 'factura_cancelada':
            default['estado_factura'] = 'factura_no_generada'
            default['folio_fiscal'] = ''
            default['fecha_factura'] = None
            default['factura_cfdi'] = False
        return super(Facturaglobal, self).copy(default=default)

    @api.depends('number')
    def _get_number_folio(self):
        if self.number:
            self.number_folio = self.number.replace('FG', '').replace('/', '')

    @api.model
    def _get_amount_2_text(self, amount_total):
        return amount_to_text_es_MX.get_amount_to_text(self, amount_total, 'es_cheque', self.currency_id.name)

    @api.depends('factura_line_ids.price_subtotal')
    def _compute_amount(self):
        round_curr = self.currency_id.round
        self.amount_untaxed = sum(line.price_subtotal for line in self.factura_line_ids)
        self.amount_total = sum(round_curr(line.price_total) for line in self.factura_line_ids)
        self.amount_tax = self.amount_total - self.amount_untaxed

    @api.model
    def _default_journal(self):
        company_id = self._context.get('default_company_id', self.env.company.id)
        if not self.journal_id:
            return self.env['account.journal'].search([('type', '=', 'sale'),('company_id', '=', company_id)], limit=1)

    @api.model
    def _default_currency(self):
        ''' Get the default currency from either the journal, either the default journal's company. '''
        journal = self._default_journal()
        return journal.company_id.currency_id

    journal_id = fields.Many2one('account.journal', 'Diario', default=_default_journal)
    currency_id = fields.Many2one("res.currency", string="Moneda", store=True, readonly=True, tracking=True,
                                  required=True,
                                  states={'draft': [('readonly', False)]}, default=_default_currency)

    @api.model
    def create(self, vals):
        if vals.get('number', _('Draft Invoice')) == _('Draft Invoice'):
            vals['number'] = self.env['ir.sequence'].next_by_code('factura.global') or _('Draft Invoice')
        result = super(Facturaglobal, self).create(vals)
        return result

    def action_valid(self):
        self.write({'state': 'valid'})
        self.invoice_date = datetime.datetime.now()

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.model
    def to_json(self):
        self.check_cfdi_values()

        if self.partner_id.vat == 'XAXX010101000' or self.partner_id.vat == 'XEXX010101000':
            zipreceptor = self.journal_id.codigo_postal or self.company_id.zip
            if self.factura_global:
                nombre = 'PUBLICO EN GENERAL'
            else:
                nombre = self.partner_id.name.upper()
        else:
            nombre = self.partner_id.name.upper()
            zipreceptor = self.partner_id.zip

        no_decimales = self.currency_id.no_decimales
        no_decimales_prod = self.currency_id.decimal_places
        no_decimales_tc = self.currency_id.no_decimales_tc

        #corregir hora
        timezone = self._context.get('tz')
        if not timezone:
            timezone = self.journal_id.tz or self.env.user.partner_id.tz or 'America/Mexico_City'
        # timezone = tools.ustr(timezone).encode('utf-8')

        local = pytz.timezone(timezone)
        if not self.fecha_factura:
           naive_from = datetime.datetime.now()
        else:
           naive_from = self.fecha_factura
        local_dt_from = naive_from.replace(tzinfo=pytz.UTC).astimezone(local)
        date_from = local_dt_from.strftime ("%Y-%m-%dT%H:%M:%S")
        if not self.fecha_factura:
           self.fecha_factura = datetime.datetime.now()

        if self.currency_id.name == 'MXN':
           tipocambio = 1
        else:
           tipocambio = self.set_decimals(1 / self.currency_id.with_context(date=self.invoice_date).rate, no_decimales_tc)

        request_params = {
                'factura': {
                      'serie': str(re.sub('[^a-z]','', self.number)) + str(re.sub('[^A-Z]','', self.number)),
                      'folio': str(re.sub('[^0-9]','', self.number)),
                      'fecha_expedicion': date_from,
                      'forma_pago': self.forma_pago_id.code,
                      'subtotal': self.amount_untaxed,
                      'descuento': 0,
                      'moneda': self.currency_id.name,
                      'tipocambio': tipocambio,
                      'total': self.amount_total,
                      'tipocomprobante': self.tipo_comprobante,
                      'metodo_pago': self.methodo_pago,
                      'LugarExpedicion': self.journal_id.codigo_postal or self.company_id.zip,
                      'Confirmacion': self.confirmacion,
                      'Exportacion': '01',
                },
                'emisor': {
                      'rfc': self.company_id.vat.upper(),
                      'nombre': self.company_id.nombre_fiscal.upper(),
                      'RegimenFiscal': self.company_id.regimen_fiscal_id.code,
                      #'FacAtrAdquirente': self.facatradquirente,
                },
                'receptor': {
                      'nombre': nombre,
                      'rfc': self.partner_id.vat.upper(),
                      'ResidenciaFiscal': self.partner_id.residencia_fiscal,
                      'NumRegIdTrib': self.partner_id.registro_tributario,
                      'UsoCFDI': self.uso_cfdi_id.code,
                      'RegimenFiscalReceptor': self.partner_id.regimen_fiscal_id.code,
                      'DomicilioFiscalReceptor': zipreceptor,
                },
                'informacion': {
                      'cfdi': '4.0',
                      'sistema': 'odoo15',
                      'version': '1',
                      'api_key': self.company_id.proveedor_timbrado,
                      'modo_prueba': self.company_id.modo_prueba,
                },
        }

        if self.factura_global:
           request_params.update({
                'InformacionGlobal': {
                      'Periodicidad': self.fg_periodicidad,
                      'Meses': self.fg_meses,
                      'Año': self.fg_ano,
                },
           })

        amount_total = 0.0
        amount_untaxed = 0.0
        subtotal = 0
        total = 0
        discount = 0
        tras_tot = 0
        ret_tot = 0
        tax_grouped_tras = {}
        tax_grouped_ret = {}
        tax_local_ret = []
        tax_local_tras = []
        tax_local_ret_tot = 0
        tax_local_tras_tot = 0
        items = {'numerodepartidas': len(self.factura_line_ids)}
        invoice_lines = []
        for line in self.factura_line_ids:
            if line.quantity <= 0:
                continue

            if not line.product_id.clave_producto:
                self.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise UserError(_('El producto %s no tiene clave del SAT configurado.') % (line.product_id.name))
            if not line.product_id.cat_unidad_medida.clave:
                self.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise UserError(_('El producto %s no tiene unidad de medida del SAT configurado.') % (line.product_id.name))

            price_wo_discount = round(line.price_unit * (1 - (line.discount / 100.0)), no_decimales_prod)

            taxes_prod = line.invoice_line_tax_ids.compute_all(price_wo_discount, line.currency_id, line.quantity,
                                                               product=line.product_id,
                                                               partner=line.factura_global_id.partner_id)
            tax_ret = []
            tax_tras = []
            tax_items = {}
            tax_included = 0
            for taxes in taxes_prod['taxes']:
                tax = self.env['account.tax'].browse(taxes['id'])
                if not tax.impuesto:
                   self.write({'proceso_timbrado': False})
                   self.env.cr.commit()
                   raise UserError(_('El impuesto %s no tiene clave del SAT configurado.') % (tax.name))
                if not tax.tipo_factor:
                   self.write({'proceso_timbrado': False})
                   self.env.cr.commit()
                   raise UserError(_('El impuesto %s no tiene tipo de factor del SAT configurado.') % (tax.name))
                if tax.impuesto != '004':
                   key = taxes['id']
                   if tax.price_include or tax.amount_type == 'division':
                       tax_included += taxes['amount']

                   if taxes['amount'] >= 0.0:
                      if tax.tipo_factor == 'Exento':
                         tax_tras.append({'Base': self.set_decimals(taxes['base'], no_decimales_prod),
                                           'Impuesto': tax.impuesto,
                                           'TipoFactor': tax.tipo_factor,})
                      elif tax.tipo_factor == 'Cuota':
                         tax_tras.append({'Base': self.set_decimals(line.quantity, no_decimales_prod),
                                           'Impuesto': tax.impuesto,
                                           'TipoFactor': tax.tipo_factor,
                                           'TasaOCuota': self.set_decimals(tax.amount,6),
                                           'Importe': self.set_decimals(taxes['amount'], no_decimales_prod),})
                      else:
                         tax_tras.append({'Base': self.set_decimals(taxes['base'], no_decimales_prod),
                                           'Impuesto': tax.impuesto,
                                           'TipoFactor': tax.tipo_factor,
                                           'TasaOCuota': self.set_decimals(tax.amount / 100.0,6),
                                           'Importe': self.set_decimals(taxes['amount'], no_decimales_prod),})
                      tras_tot += taxes['amount']
                      val = {'tax_id': taxes['id'],
                             'base': taxes['base'] if tax.tipo_factor != 'Cuota' else line.quantity,
                             'amount': taxes['amount'],}
                      if key not in tax_grouped_tras:
                          tax_grouped_tras[key] = val
                      else:
                          tax_grouped_tras[key]['base'] += val['base'] if tax.tipo_factor != 'Cuota' else line.quantity
                          tax_grouped_tras[key]['amount'] += val['amount']
                   else:
                      tax_ret.append({'Base': self.set_decimals(taxes['base'], no_decimales_prod),
                                      'Impuesto': tax.impuesto,
                                      'TipoFactor': tax.tipo_factor,
                                      'TasaOCuota': self.set_decimals(tax.amount / 100.0 * -1, 6),
                                      'Importe': self.set_decimals(taxes['amount'] * -1, no_decimales_prod),})
                      ret_tot += taxes['amount'] * -1
                      val = {'tax_id': taxes['id'],
                             'base': taxes['base'],
                             'amount': taxes['amount'],}
                      if key not in tax_grouped_ret:
                          tax_grouped_ret[key] = val
                      else:
                          tax_grouped_ret[key]['base'] += val['base']
                          tax_grouped_ret[key]['amount'] += val['amount']
                else: #impuestos locales
                   if taxes['amount'] >= 0.0:
                      tax_local_tras_tot += taxes['amount']
                      tax_local_tras.append({'ImpLocTrasladado': tax.impuesto_local,
                                             'TasadeTraslado': self.set_decimals(tax.amount / 100.0,6),
                                             'Importe': self.set_decimals(taxes['amount'], no_decimales),})
                   else:
                      tax_local_ret_tot += taxes['amount']
                      tax_local_ret.append({'ImpLocRetenido': tax.impuesto_local,
                                            'TasadeRetencion': self.set_decimals(tax.amount / 100.0 * -1,6),
                                            'Importe': self.set_decimals(taxes['amount'] * -1, no_decimales),})

            if tax_tras:
               tax_items.update({'Traslados': tax_tras})
            if tax_ret:
               tax_items.update({'Retenciones': tax_ret})

            total_wo_discount = round(line.price_unit * line.quantity - tax_included, no_decimales_prod)
            discount_prod = round(total_wo_discount - line.price_subtotal, no_decimales_prod) if line.discount else 0
            precio_unitario = round(total_wo_discount / line.quantity, no_decimales_prod)
            subtotal += total_wo_discount
            discount += discount_prod

            product_string = line.product_id.code and line.product_id.code[:100] or ''
            if product_string == '':
               if line.name.find(']') > 0:
                  product_string = line.name[line.name.find('[')+len('['):line.name.find(']')] or ''
            description = line.name
            if line.name.find(']') > 0:
                 description = line.name[line.name.find(']') + 2:]

            if self.tipo_comprobante == 'T':
                invoice_lines.append({'cantidad': self.set_decimals(line.quantity,6),
                                      'unidad': line.product_id.cat_unidad_medida.descripcion,
                                      'NoIdentificacion': self.clean_text(product_string),
                                      'valorunitario': self.set_decimals(precio_unitario, no_decimales_prod),
                                      'importe': self.set_decimals(total_wo_discount, no_decimales_prod),
                                      'descripcion': self.clean_text(description),
                                      'ClaveProdServ': line.product_id.clave_producto,
                                      'ObjetoImp': line.product_id.objetoimp,
                                      'ClaveUnidad': line.product_id.cat_unidad_medida.clave})
            else:
                invoice_lines.append({'cantidad': self.set_decimals(line.quantity,6),
                                      'unidad': line.product_id.cat_unidad_medida.descripcion,
                                      'NoIdentificacion': self.clean_text(product_string),
                                      'valorunitario': self.set_decimals(precio_unitario, no_decimales_prod),
                                      'importe': self.set_decimals(total_wo_discount, no_decimales_prod),
                                      'descripcion': self.clean_text(description),
                                      'ClaveProdServ': line.product_id.clave_producto,
                                      'ClaveUnidad': line.product_id.cat_unidad_medida.clave,
                                      'Impuestos': tax_items and tax_items or '',
                                      'Descuento': self.set_decimals(discount_prod, no_decimales_prod),
                                      'ObjetoImp': line.product_id.objetoimp,})

        tras_tot = round(tras_tot, no_decimales)
        ret_tot = round(ret_tot, no_decimales)
        tax_local_tras_tot = round(tax_local_tras_tot, no_decimales)
        tax_local_ret_tot = round(tax_local_ret_tot, no_decimales)
        discount = round(discount, no_decimales)
        if tax_grouped_tras or tax_grouped_ret:
                impuestos = {}
                retenciones = []
                traslados = []
                if tax_grouped_tras:
                   for line in tax_grouped_tras.values():
                       tax = self.env['account.tax'].browse(line['tax_id'])
                       if tax.tipo_factor == 'Exento':
                          tasa_tr = ''
                       elif tax.tipo_factor == 'Cuota':
                          tasa_tr = self.set_decimals(tax.amount, 6)
                       else:
                          tasa_tr = self.set_decimals(tax.amount / 100.0, 6)
                       traslados.append({'impuesto': tax.impuesto,
                                         'TipoFactor': tax.tipo_factor,
                                         'tasa': tasa_tr,
                                         'importe': self.set_decimals(line['amount'], no_decimales) if tax.tipo_factor != 'Exento' else '',
                                         'base': self.set_decimals(line['base'], no_decimales),
                                         'tax_id': line['tax_id'],
                                         })
                   impuestos.update({'translados': traslados, 'TotalImpuestosTrasladados': self.set_decimals(tras_tot, no_decimales)})
                if tax_grouped_ret:
                   for line in tax_grouped_ret.values():
                       tax = self.env['account.tax'].browse(line['tax_id'])
                       retenciones.append({'impuesto': tax.impuesto,
                                         'TipoFactor': tax.tipo_factor,
                                         'tasa': self.set_decimals(float(tax.amount) / 100.0 * -1, 6),
                                         'importe': self.set_decimals(line['amount'] * -1, no_decimales),
                                         'base': self.set_decimals(line['base'], no_decimales),
                                         'tax_id': line['tax_id'],
                                         })
                   impuestos.update({'retenciones': retenciones, 'TotalImpuestosRetenidos': self.set_decimals(ret_tot, no_decimales)})
                request_params.update({'impuestos': impuestos})
                self.tax_payment = json.dumps(impuestos)

        if tax_local_ret or tax_local_tras:
           if tax_local_tras and not tax_local_ret:
               request_params.update({'implocal10': {'TotaldeTraslados': tax_local_tras_tot, 'TotaldeRetenciones': tax_local_ret_tot, 'TrasladosLocales': tax_local_tras,}})
           if tax_local_ret and not tax_local_tras:
               request_params.update({'implocal10': {'TotaldeTraslados': tax_local_tras_tot, 'TotaldeRetenciones': tax_local_ret_tot * -1, 'RetencionesLocales': tax_local_ret,}})
           if tax_local_ret and tax_local_tras:
               request_params.update({'implocal10': {'TotaldeTraslados': tax_local_tras_tot, 'TotaldeRetenciones': tax_local_ret_tot * -1, 'TrasladosLocales': tax_local_tras, 'RetencionesLocales': tax_local_ret,}})

        if self.tipo_comprobante == 'T':
            request_params['factura'].update({'subtotal': '0.00','total': '0.00'})
        else:
            request_params['factura'].update({'descuento': self.set_decimals(discount, no_decimales),
                                              'subtotal': self.set_decimals(subtotal, no_decimales),
                                              'total':  self.set_decimals(subtotal + tras_tot - ret_tot - discount + tax_local_ret_tot + tax_local_tras_tot, no_decimales)})

        request_params.update({'conceptos': invoice_lines})

        return request_params

    def set_decimals(self, amount, precision):
        if amount is None or amount is False:
            return None
        return '%.*f' % (precision, amount)

    def clean_text(self, text):
        clean_text = text.replace('\n', ' ').replace('\\', ' ').replace('-', ' ').replace('/', ' ').replace('|', ' ')
        clean_text = clean_text.replace(',', ' ').replace(';', ' ').replace('>', ' ').replace('<', ' ')
        return clean_text[:1000]

    def check_cfdi_values(self):
        if not self.company_id.vat:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('El emisor no tiene RFC configurado.'))
        if not self.company_id.name:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('El emisor no tiene nombre configurado.'))
        if not self.partner_id.vat:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('El receptor no tiene RFC configurado.'))
        if not self.uso_cfdi_id:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('La factura no tiene uso de cfdi configurado.'))
        if not self.tipo_comprobante:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('El emisor no tiene tipo de comprobante configurado.'))
        if self.tipo_comprobante != 'T' and not self.methodo_pago:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('La factura no tiene método de pago configurado.'))
        if self.tipo_comprobante != 'T' and not self.forma_pago_id:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('La factura no tiene forma de pago configurado.'))
        if not self.company_id.regimen_fiscal_id:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('El emisor no régimen fiscal configurado.'))
        if not self.journal_id.codigo_postal and not self.company_id.zip:
            self.write({'proceso_timbrado': False})
            self.env.cr.commit()
            raise UserError(_('El emisor no tiene código postal configurado.'))

    def _set_data_from_xml(self, xml_invoice):
        if not xml_invoice:
            return None
        NSMAP = {
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'cfdi': 'http://www.sat.gob.mx/cfd/4',
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
        }

        xml_data = etree.fromstring(xml_invoice)
        Complemento = xml_data.findall('cfdi:Complemento', NSMAP)

        for complementos in Complemento:
            TimbreFiscalDigital = complementos.find('tfd:TimbreFiscalDigital', NSMAP)
            if TimbreFiscalDigital:
                break

        #self.tipocambio = xml_data.attrib['TipoCambio']
        self.moneda = xml_data.attrib['Moneda']
        self.numero_cetificado = xml_data.attrib['NoCertificado']
        self.cetificaso_sat = TimbreFiscalDigital.attrib['NoCertificadoSAT']
        self.fecha_certificacion = TimbreFiscalDigital.attrib['FechaTimbrado']
        self.selo_digital_cdfi = TimbreFiscalDigital.attrib['SelloCFD']
        self.selo_sat = TimbreFiscalDigital.attrib['SelloSAT']
        self.folio_fiscal = TimbreFiscalDigital.attrib['UUID']
        self.invoice_datetime = xml_data.attrib['Fecha']
#        if not self.fecha_factura:
#            self.fecha_factura = self.invoice_datetime.replace('T', ' ')
        version = TimbreFiscalDigital.attrib['Version']
        self.cadena_origenal = '||%s|%s|%s|%s|%s||' % (version, self.folio_fiscal, self.fecha_certificacion,
                                                       self.selo_digital_cdfi, self.cetificaso_sat)

        options = {'width': 275 * mm, 'height': 275 * mm}
        amount_str = str(self.amount_total).split('.')
        qr_value = 'https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?&id=%s&re=%s&rr=%s&tt=%s.%s&fe=%s' % (
            self.folio_fiscal,
            self.company_id.vat,
            self.partner_id.vat,
            amount_str[0].zfill(10),
            amount_str[1].ljust(6, '0'),
            self.selo_digital_cdfi[-8:],
        )
        self.qr_value = qr_value
        ret_val = createBarcodeDrawing('QR', value=qr_value, **options)
        self.qrcode_image = base64.encodebytes(ret_val.asString('jpg'))

    def action_cfdi_generate(self):
        # after validate, send invoice data to external system via http post
        for invoice in self:
            if invoice.proceso_timbrado:
                return True
            else:
               invoice.write({'proceso_timbrado': True})
               self.env.cr.commit()
            if invoice.estado_factura == 'factura_correcta':
                if invoice.folio_fiscal:
                    invoice.write({'factura_cfdi': True})
                    return True
                else:
                    invoice.write({'proceso_timbrado': False})
                    self.env.cr.commit()
                    raise UserError(_('Error para timbrar factura, Factura ya generada.'))
            if invoice.estado_factura == 'factura_cancelada':
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise UserError(_('Error para timbrar factura, Factura ya generada y cancelada.'))

            values = invoice.to_json()
            if invoice.company_id.proveedor_timbrado == 'multifactura':
                url = '%s' % ('http://facturacion.itadmin.com.mx/api/invoice')
            elif invoice.company_id.proveedor_timbrado == 'multifactura2':
                url = '%s' % ('http://facturacion2.itadmin.com.mx/api/invoice')
            elif invoice.company_id.proveedor_timbrado == 'multifactura3':
                url = '%s' % ('http://facturacion3.itadmin.com.mx/api/invoice')
            elif invoice.company_id.proveedor_timbrado == 'gecoerp':
                if self.company_id.modo_prueba:
                    url = '%s' % ('https://itadmin.gecoerp.com/invoice/?handler=OdooHandler33')
                else:
                    url = '%s' % ('https://itadmin.gecoerp.com/invoice/?handler=OdooHandler33')
            else:
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise UserError(_('Error, falta seleccionar el servidor de timbrado en la configuración de la compañía.'))

            try:
                response = requests.post(url,
                                         auth=None, verify=False, data=json.dumps(values),
                                         headers={"Content-type": "application/json"})
            except Exception as e:
                error = str(e)
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                if "Name or service not known" in error or "Failed to establish a new connection" in error:
                    raise Warning("No se pudo conectar con el servidor.")
                else:
                    raise Warning(error)

            if "Whoops, looks like something went wrong." in response.text:
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise Warning("Error en el proceso de timbrado, espere un minuto y vuelva a intentar timbrar nuevamente. \nSi el error aparece varias veces reportarlo con la persona de sistemas.")
            else:
                json_response = response.json()
            estado_factura = json_response['estado_factura']
            if estado_factura == 'problemas_factura':
                invoice.write({'proceso_timbrado': False})
                self.env.cr.commit()
                raise UserError(_(json_response['problemas_message']))
            # Receive and stroe XML invoice
            if json_response.get('factura_xml'):
                invoice._set_data_from_xml(base64.b64decode(json_response['factura_xml']))
                file_name = invoice.number.replace('/', '_') + '.xml'
                self.env['ir.attachment'].sudo().create(
                    {
                        'name': file_name,
                        'datas': json_response['factura_xml'],
                        # 'datas_fname': file_name,
                        'res_model': self._name,
                        'res_id': invoice.id,
                        'type': 'binary'
                    })

            invoice.write({'estado_factura': estado_factura,
                           'factura_cfdi': True,
                           'proceso_timbrado': False})
            invoice.message_post(body="CFDI emitido")
        return True

    def action_cancel_global_invoice(self):
        for invoice in self:
            if invoice.source_document:
               docs = invoice.source_document.split(',')
               docs = [doc.strip() for doc in docs]
               pos_order = self.env['pos.order'].search([('name', 'in', docs)])
               # pos_order.write({'state': 'done'})
               for order in pos_order:
                   if order.state == 'invoiced':
                       order.state = 'done'
                       order.factura_global_id = False

    def action_cfdi_cancel(self):
        for invoice in self:
            if invoice.factura_cfdi:
                if invoice.estado_factura == 'factura_cancelada':
                    pass
                    # raise UserError(_('La factura ya fue cancelada, no puede volver a cancelarse.'))
                if not invoice.company_id.contrasena:
                  raise UserError(_('El campo de contraseña de los certificados está vacío.'))
                domain = [
                    ('res_id', '=', invoice.id),
                    ('res_model', '=', invoice._name),
                    ('name', '=', invoice.number.replace('/', '_') + '.xml')]
                xml_file = self.env['ir.attachment'].search(domain)
                if not xml_file:
                  raise UserError(_('No se encontró el archivo XML para enviar a cancelar.'))
                values = {
                    'rfc': invoice.company_id.vat,
                    'api_key': invoice.company_id.proveedor_timbrado,
                    'uuid': invoice.folio_fiscal,
                    'folio': invoice.number.replace('FG','').replace('/',''),
                    'serie_factura': invoice.journal_id.serie_diario or invoice.company_id.serie_factura,
                    'modo_prueba': invoice.company_id.modo_prueba,
                    'certificados': {
                    #    'archivo_cer': archivo_cer.decode("utf-8"),
                    #    'archivo_key': archivo_key.decode("utf-8"),
                        'contrasena': invoice.company_id.contrasena,
                    },
                    'xml': xml_file[0].datas.decode("utf-8"),
                    'motivo': self.env.context.get('motivo_cancelacion',False),
                    'foliosustitucion': self.env.context.get('foliosustitucion',''),
                }
                if self.company_id.proveedor_timbrado == 'multifactura':
                    url = '%s' % ('http://facturacion.itadmin.com.mx/api/refund')
                elif invoice.company_id.proveedor_timbrado == 'multifactura2':
                    url = '%s' % ('http://facturacion2.itadmin.com.mx/api/refund')
                elif invoice.company_id.proveedor_timbrado == 'multifactura3':
                    url = '%s' % ('http://facturacion3.itadmin.com.mx/api/refund')
                elif self.company_id.proveedor_timbrado == 'gecoerp':
                    if self.company_id.modo_prueba:
                        url = '%s' % ('https://itadmin.gecoerp.com/refund/?handler=OdooHandler33')
                    else:
                        url = '%s' % ('https://itadmin.gecoerp.com/refund/?handler=OdooHandler33')
                else:
                    raise UserError(_('Error, falta seleccionar el servidor de timbrado en la configuración de la compañía.'))

                try:
                    response = requests.post(url,
                                             auth=None, verify=False, data=json.dumps(values),
                                             headers={"Content-type": "application/json"})
                except Exception as e:
                    error = str(e)
                    if "Name or service not known" in error or "Failed to establish a new connection" in error:
                        raise Warning("No se pudo conectar con el servidor.")
                    else:
                        raise Warning(error)

                if "Whoops, looks like something went wrong." in response.text:
                    raise Warning("Error en el proceso de timbrado, espere un minuto y vuelva a intentar timbrar nuevamente. \nSi el error aparece varias veces reportarlo con la persona de sistemas.")

                json_response = response.json()

                log_msg = ''
                if json_response['estado_factura'] == 'problemas_factura':
                    raise UserError(_(json_response['problemas_message']))
                elif json_response['estado_factura'] == 'solicitud_cancelar':
                    # invoice.write({'estado_factura': json_response['estado_factura']})
                    log_msg = "Se solicitó cancelación de CFDI"
                    # raise Warning(_(json_response['problemas_message']))
                elif json_response.get('factura_xml', False):
                    file_name = 'CANCEL_' + invoice.number.replace('/', '_') + '.xml'
                    self.env['ir.attachment'].sudo().create(
                        {
                            'name': file_name,
                            'datas': json_response['factura_xml'],
                            # 'datas_fname': file_name,
                            'res_model': self._name,
                            'res_id': invoice.id,
                            'type': 'binary'
                        })
                    log_msg = "CFDI Cancelado"
                invoice.write({'estado_factura': json_response['estado_factura']})
                # invoice.message_post(body=log_msg)

    def action_cfdi_rechazada(self):
        for invoice in self:
            if invoice.factura_cfdi:
                if invoice.estado_factura == 'solicitud_rechazada' or invoice.estado_factura == 'solicitud_cancelar':
                    invoice.estado_factura = 'factura_correcta'

    def send_factura_mail(self):
        self.ensure_one()
        template = self.env.ref('custom_invoice.email_template_factura_global', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)

        ctx = dict()
        ctx.update({
            'default_model': 'factura.global',
            'default_res_id': self.id,
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def unlink(self):
        raise UserError("Los registros no se pueden borrar, solo cancelar.")

class FacturaGlobalMail(models.Model):
    _name = "factura.global.mail"
    _inherit = ['mail.thread']
    _description = "Factura global Mail"

    factura_id = fields.Many2one('factura.global', string='Factura Global')
    name = fields.Char(related='factura_id.number')
    partner_id = fields.Many2one(related='factura_id.partner_id')
    company_id = fields.Many2one(related='factura_id.company_id')


class MailTemplate(models.Model):
    "Templates for sending email"
    _inherit = 'mail.template'

    @api.model
    def _get_file(self, url):
        url = url.encode('utf8')
        filename, headers = urllib.urlretrieve(url)
        fn, file_extension = os.path.splitext(filename)
        return filename, file_extension.replace('.', '')

    def generate_email(self, res_ids, fields=None):
        results = super(MailTemplate, self).generate_email(res_ids, fields=fields)

        if isinstance(res_ids, (int)):
            res_ids = [res_ids]
#         res_ids_to_templates = super(MailTemplate, self).get_email_template(res_ids)

        # templates: res_id -> template; template -> res_ids
#         templates_to_res_ids = {}
#         for res_id, template in res_ids_to_templates.items():
#             templates_to_res_ids.setdefault(template, []).append(res_id)
        
        template_id = self.env.ref('custom_invoice.email_template_factura_global')
#         for template, template_res_ids in templates_to_res_ids.items():
        for lang, (template, template_res_ids) in self._classify_per_lang(res_ids).items():
            if template.id  == template_id.id:
                for res_id in template_res_ids:
                    invoice = self.env[template.model].browse(res_id)
                    if not invoice.factura_cfdi:
                        continue
                    if invoice.estado_factura == 'factura_correcta' or invoice.estado_factura == 'solicitud_cancelar':
                        domain = [
                            ('res_id', '=', invoice.id),
                            ('res_model', '=', invoice._name),
                            ('name', '=', invoice.number.replace('/', '_') + '.xml')]
                        xml_file = self.env['ir.attachment'].search(domain, limit=1)
                        attachments = results[res_id]['attachments'] or []
                        if xml_file:
                           attachments.append(('CDFI_' + invoice.number.replace('/', '_') + '.xml', xml_file.datas))
                    else:
                        domain = [
                            ('res_id', '=', invoice.id),
                            ('res_model', '=', invoice._name),
                            ('name', '=', 'CANCEL_' + invoice.number.replace('/', '_') + '.xml')]
                        xml_file = self.env['ir.attachment'].search(domain, limit=1)
                        attachments = []
                        if xml_file:
                           attachments.append(('CDFI_CANCEL_' + invoice.number.replace('/', '_') + '.xml', xml_file.datas))
                    results[res_id]['attachments'] = attachments
        return results

