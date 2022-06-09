# -*- coding: utf-8 -*-
{
	'name': "Organigrama San Luis",
	'summary': """Organigrama de San Luis""",
	'description': """Organigrama""",
	'author': "Sinergia",
	'category': 'Human Resources',
	'version': '2.1',
	'license': 'OPL-1',
	'depends': ['hr'],
	'price': 20.00,
	'currency': 'EUR',
	'support': 'alejandro.avila@sinergia-e.com',
	'data': [
		'security/ir.model.access.csv',
		'views/org_chart_views.xml'
	],
	'images': [
		'static/src/img/main_screenshot.png'
	],
	'installable': True,
	'application': True,
	'auto_install': False,
	'assets': {
        'web.assets_backend': [
			'org_chart_employee_pro/static/js/org_chart_employee.js',
			'org_chart_employee_pro/static/js/jquery_orgchart.js',
			'org_chart_employee_pro/static/js/other.js',
			'org_chart_employee_pro/static/js/jspdf_min.js',
			'org_chart_employee_pro/static/js/html2canvas_min.js',
			'org_chart_employee_pro/static/src/css/jquery_orgchart.css',
			'org_chart_employee_pro/static/src/css/style.css',
        ],
        'web.assets_qweb': [
            'org_chart_employee_pro/static/src/xml/org_chart_employee.xml',
        ],
    },
}
