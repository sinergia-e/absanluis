# Copyright 2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Politica de Facturacion San Luis",
    "summary": """
        Seleccionar la politica de facturacion en la orden""",
    "author": "Sinergia",
    "website": "https://www.sinergia.click",
    "category": "Sales Management",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["sale_stock"],
    "data": [
        "views/product_template_view.xml",
        "views/res_config_settings_view.xml",
        "views/sale_view.xml",
    ],
    "post_init_hook": "post_init_hook",
}
