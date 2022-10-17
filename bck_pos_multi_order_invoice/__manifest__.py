# -*- coding: utf-8 -*-
{
    'name': 'Factura Global POS (Mexico SAT)',

    'summary': """
    Con este módulo puedes generar una Factura Global de pedidos de Punto de Venta de sesiones abiertas o cerradas.""",

    'description': """
    Factura Global de pedidos de Punto de Venta que cumple con los requisitos del SAT o factura genérica para cualquier cliente.""",

    'author': 'Sinergia',
    'license': 'OPL-1',
    'website': 'http://www.sinergia-e.com',
    'currency': 'USD',
    'price': 132.00,
    'images': ['static/description/banner.png'],
    'category': 'Point of Sale',
    'version': '15.0.1.5',
    'depends': [
        'base',
        'uom',
        'point_of_sale',
        'account',
        'bck_l10n_mx_partner_edi_defaults_invoice',
    ],

    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/pos_order_views.xml',
        'views/res_config_setting.xml',
        'views/pos_payment_method_views.xml',
        'views/account_move_views.xml',
        'views/product_template_views.xml',
        'views/l10n_mx_edi_cfdiv33.xml',
        'wizard/wizard_pos_invoice.xml',
        'data/global_invoice_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_check',
}
