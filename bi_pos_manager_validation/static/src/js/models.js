odoo.define('bi_pos_manager_validation.pos', function (require) {
'use strict';

	var models = require('point_of_sale.models');
	var core = require('web.core');
	var _t = core._t;
	const { Gui } = require('point_of_sale.Gui');

	models.load_fields('res.users',['pos_security_pin']);

	var posorder_super = models.Order.prototype;
	models.Order = models.Order.extend({
		initialize: function(attr, options) {
			posorder_super.initialize.call(this,attr,options);
			let pos_otp = this.pos.get('otp');
			if(!pos_otp){
				this.pos.set('otp',false);
			}
		},

		async checkPswd(){
			let self = this;
			let res = false;
			const { confirmed, payload } = await Gui.showPopup('NumberPopup', {
				title: _t('Manager Password'),
				isPassword: true,
			});
			if (confirmed) {
				let user_passd;
				let users = self.pos.config.user_id;
				for (let i = 0; i < self.pos.users.length; i++) {
					if (self.pos.users[i].id === users[0]) {
						user_passd = self.pos.users[i].pos_security_pin;
					}
				}
				if (payload == user_passd){
					res =  true;
					self.pos.set('otp',true);
				}else{
					Gui.showPopup('ErrorPopup', {
						title: _t('Invalid Password'),
						body: _t('Wrong Password'),
					});
					return false;
				}
			}
			return res;
		},
	});
});
