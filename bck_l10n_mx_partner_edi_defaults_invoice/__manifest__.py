# -*- coding: utf-8 -*-
{
    
    'name': 'Uso y Forma de Pago por defecto (Localización Mexicana)',

    'summary': """
    Es posible definir valores por defecto de "Uso" y "Forma de Pago" del cliente.""",

    'description': """
    Al crear una factura y seleccionar el cliente, se heredarán los campos "Uso" y "Forma de Pago" del cliente.
    """,

    'author': 'Sinergia',
    'support': 'soporte@sinergia-e.com',
    'license': 'OPL-1',
    'website': 'http://www.sinergia-e.com',
    'currency': 'USD',
    'price': 17.00,
    'category': 'Invoice',
    'version': '15.0.1.0',

    'depends': ['base', 'account', 'l10n_mx_edi'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'pre_init_hook': 'pre_init_check',
}
