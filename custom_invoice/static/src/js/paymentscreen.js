odoo.define('custom_invoice.PaymentScreen', function(require) {
    'use strict';
	
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');

    const CDFIDetailPopupWidget = PaymentScreen =>
        class extends PaymentScreen {
             toggleIsToInvoice() {
             
            	const { confirmed } = this.showPopup('CDFIDetailPopupWidget',{});
          	                 
            	 return super.toggleIsToInvoice(...arguments);
                }
            
        };
    
    console.log(CDFIDetailPopupWidget)
    Registries.Component.extend(PaymentScreen, CDFIDetailPopupWidget);

    return PaymentScreen;
});
