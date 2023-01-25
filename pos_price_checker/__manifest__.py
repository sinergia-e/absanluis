# -*- coding: utf-8 -*-


{
       
    'name': 'Verificadores San Luis',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'Sinergia',
    'summary': 'Usa terminal como Verificador.',
    'description': """

=======================
Permite usar POS como verificador.

""",
    'depends': ['point_of_sale'],
    'data': [
            'views/views.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_price_checker/static/src/js/jquery-ui.css',
            'pos_price_checker/static/src/js/pos.js',
            'pos_price_checker/static/src/css/pos.css',
        ],
        'web.assets_qweb': [
            'pos_price_checker/static/src/xml/**/*',
        ],
    },
    'images': [
        'static/description/sele.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 100,
    'currency': 'EUR',
}
