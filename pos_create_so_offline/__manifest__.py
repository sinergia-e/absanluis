# -*- coding: utf-8 -*-

{
    'name': 'Pedidos OffLine',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'Sinergia',
    'summary': "Modulo para Vendedores de ruta." ,
    'description': "Crea pedidos sin conexion.",
    'depends': ['point_of_sale','sale'],
    'data': [
        'views/views.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_create_so_offline/static/src/js/pos.js',
        ],
        'web.assets_qweb': [
            'pos_create_so_offline/static/src/xml/**/*',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 99,
    'currency': 'EUR',
}
