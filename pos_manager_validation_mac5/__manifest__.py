{

    'name': 'Validacion de supervisor POS',
    'version': '15.0.1.2',
    'summary': """Validacion""",
    'description': """


""",
    'category': 'Point of Sale',
    'author': 'MAC5',
    'contributors': ['MAC5'],
    'website': 'www.sinergia.click',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'views/res_users_views.xml',
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_manager_validation_mac5/static/src/js/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/pos_ui_validate.png'],
    'price': 69.99,
    'currency': 'EUR',
    'support': 'alejandro.avila@sinergia-e.com',
    'license': 'OPL-1',
}
