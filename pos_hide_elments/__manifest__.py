
{
    "name": "Ocultar Elementos Pos",
    "summary": "Este campo permite quitar elementos en el pos",
    "version": "15.0.1.0.0",
    "author": "Jesus pozzo",
    "website": "",
    "license": "AGPL-3",
    "category": "Point Of Sale",
    "depends": ["point_of_sale"],
    "data": [

    ],
    'assets': {
        'point_of_sale.assets': [
        ],
        'web.assets_qweb': ['pos_hide_elments/static/src/xml/ProductInfoPopup.xml'],
    },

    "installable": True,
}
