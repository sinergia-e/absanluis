# -*- coding: utf-8 -*-
{
    'name': "Reporte de cambios de precio San Luis",
    'version': '1.0',
    'summary': "Precios que cambiaron de precio",
    'author': 'Sinergia',
    'category': 'Management System',
    'sequence': 9,

    'website': '',

    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'reports/product_sales_price_update_report_template.xml',
        # 'reports/report.xml',
        'views/report_menu.xml',
        'views/settings.xml',
        'wizards/wizard_view.xml',
        'data/mail_template.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'auto_install': False,
    'price': 15,
    'currency': 'USD',
    'bootstrap': True,
}
