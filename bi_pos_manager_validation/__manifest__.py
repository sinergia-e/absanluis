
{
    "name" : "Validacion de Supervisor",
    "version" : "15.0.0.0",
    "category" : "Point of Sale",
    'summary': 'Requiere aprobacion de supervisor en operaciones definidas',
    "description": """ Solicita Codigo PIN en Operaciones definidas""",
    "author": "Sinergia",
    "website" : "https://www.sinergia-e.com",
    "price": 29,
    "currency": 'MXN',
    "depends" : ['base','point_of_sale'],
    "data": [
        'views/pos_config.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'bi_pos_manager_validation/static/src/css/custom.css',
            "bi_pos_manager_validation/static/src/js/models.js",
            "bi_pos_manager_validation/static/src/js/HeaderButton.js",
            "bi_pos_manager_validation/static/src/js/NumpadWidget.js",
            "bi_pos_manager_validation/static/src/js/ProductScreen.js",
            "bi_pos_manager_validation/static/src/js/TicketScreen.js",
        ],
    },
    "auto_install": False,
    "installable": True,
    "images":["static/description/Banner.png"],
    'license': 'OPL-1',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
