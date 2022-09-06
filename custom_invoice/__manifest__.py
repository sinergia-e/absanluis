# -*- coding: utf-8 -*-
#############################################################################
#
##############################################################################

{
	
    'name': 'Punto de Venta Factura Electronica Mexico CFDI',
    'version': '15.02',
    'description': ''' Punto de Venta Factura Electronica Mexico (CFDI 4.0).
    ''',
    'category': 'Sales, Point Of Sale, Accounting',
    'author': 'IT Admin',
    'website': '',
    'depends': [
        'point_of_sale','sale','account', 'cdfi_invoice'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'reports/invoice_report.xml',
        'views/point_of_sale_view.xml',
        'views/factura_global_view.xml',
        'wizard/create_invoice_wizard.xml',
        'wizard/create_invoice_total_wizard.xml',
        'wizard/create_invoice_session_wizard.xml',
        'data/factura_global.xml',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
	],
    'assets': {
        'point_of_sale.assets': [
           "custom_invoice/static/src/js/models.js",
           "custom_invoice/static/src/js/CDFIDetailPopupWidget.js",
           "custom_invoice/static/src/js/paymentscreen.js",
           "custom_invoice/static/src/js/screens.js",

            ],
        'web.assets_qweb': [
            'custom_invoice/static/src/xml/CDFIDetailPopupWidget.xml',
            'custom_invoice/static/src/xml/pos.xml',
            'custom_invoice/static/src/xml/regimen_fiscal.xml',

        ],
    },
    'application': False,
    'installable': True,
    'price': 0.00,
    'currency': 'USD',
    'license': 'OPL-1',	
}
