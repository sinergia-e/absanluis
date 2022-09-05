{
    'name': 'Mexican POS global invoice',
    'version': '14.0.0.0.0',
    'price': 69.99,
    'currency': 'USD',
    'summary': 'Make global invoice on point of sale',
    'category': 'Point Of Sale',
    'author': 'Xmarts',
    'website': 'https://wwww.xmarts.com/',
    'license': '',
    'depends': [
        'base',
        'point_of_sale',
    ],
    'data': [
        'views/pos_config_views.xml',
        'views/pos_session_views.xml',
        'views/pos_order.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
