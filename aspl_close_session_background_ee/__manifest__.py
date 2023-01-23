# -*- coding: utf-8 -*-

{
    'name': 'Cierra Sesiones',
    'category': 'Point of Sale',
    'summary': 'Cierra Sesiones',
    'description': """
    Cierra Sesiones Automaticamente
       """,
    'author': 'Sinergia',
    'website': 'http://www.sinergia.click',
    'price': 22.00,
    'currency': 'EUR',
    'version': '1.0.0',
    'depends': ['base', 'point_of_sale'],
    'images': ['static/description/main_screenshot.png'],
    "data": [
        'security/ir.model.access.csv',
        'wizard/wizard_session_close_view.xml',
        'views/point_of_sale.xml',
        'views/pos_session_schedular.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
