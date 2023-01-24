# -*- coding: utf-8 -*-

{
    
    
    'name': 'Peso y Volumen en las ordenes',
    'version': '15.0.0.0',
    'category': 'Sales',
    'summary': 'Calcula peso y volumen en las ordenes de venta',
    'description': """
        


    """,
    'author': 'Sinergia',
    "price": 8,
    "currency": 'MXN',
    'website': 'https://www.sinergi.click',
    'depends': ['sale_management', 'stock'],
    'data': [
        'report/sale_order_report.xml',
        'views/sale_weight_views.xml',
    ],
    'demo': [],
    'test': [],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
}
