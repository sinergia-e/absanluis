
odoo.define('bi_pos_manager_validation.NumpadWidgetValidation', function(require) {
	'use strict';

	const PosComponent = require('point_of_sale.PosComponent');
	const ProductScreen = require('point_of_sale.ProductScreen');
	const NumpadWidget = require('point_of_sale.NumpadWidget');
	const Registries = require('point_of_sale.Registries');
	let models = require('point_of_sale.models');
	const Popup = require('point_of_sale.NumberPopup');
	let check_qty = true;
	let check_disc = true;
	let check_price = true;


	const NumpadWidgetValidation = (NumpadWidget) =>
		class extends NumpadWidget {
			constructor() {
				super(...arguments);
			}

	};
	Registries.Component.extend(NumpadWidget, NumpadWidgetValidation);

	return NumpadWidget;

});
