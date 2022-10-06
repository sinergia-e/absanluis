# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################

{
    'name': "Historico de precios venta/compra San Luis",
    'version': "15.0.0.0",
    'summary': "Historico de precios de venta y compra san luis.",
    'category': 'Sales',
    'description': """
    
    
    """,
    'author': "Sinergia",
    'website':"https://www.sinergia.click",
    'depends': ['base', 'sale_management', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/inherited_product.xml',
        'views/inherited_res_config_setting.xml',
    ],
    'demo': [],
    "external_dependencies": {},
    "license": "OPL-1",
    'installable': True,
    'auto_install': False,
    'images': ['static/description/banner.png'],
    "price": 0,
    "currency": 'MXN',
    
}
