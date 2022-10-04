# -*- coding: utf-8 -*-
#############################################################################
#
#    Sinergia.
#
#############################################################################

{
    'name': 'Marca o proveedor en los productos',
    'version': '15.0.1.0.0',
    'category': 'Sales',
    'summary': 'Proveedor en ventas',
    'description': 'Marca o proveedor de productos en ventas',
    'author': 'Sinergia',
    'company': 'Sinergia',
    'maintainer': 'Sinergia',
    'images': ['static/description/banner.png'],
    'website': 'https://www.sinergia.click',
    'depends': ['sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/brand_views.xml',
        'views/sale_report_views.xml'
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

}
