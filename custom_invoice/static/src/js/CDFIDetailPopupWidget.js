odoo.define('custom_invoice.CDFIDetailPopupWidget',function(require){
	'use strict';

const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');

class CDFIDetailPopupWidget extends AbstractAwaitablePopup {
    constructor() {
      super(...arguments);
    }
	getPayload() {
		return null;
	}
	confirm() {
			 debugger;
    		 var order = this.env.pos.get_order()
    		 
    		 var forma_pago  = document.getElementsByClassName("js_forma_pago")[0]
    	     var methodo_pago = document.getElementsByClassName("js_methodo_pago")[0]
    	     var uso_cfdi = document.getElementsByClassName("js_uso_cfdi")[0]		 
    	     
    	     order.forma_pago_id = forma_pago.value || undefined;
    	     order.methodo_pago = methodo_pago.value || undefined;
    	     order.uso_cfdi_id = uso_cfdi.value || undefined;
    	     
    	     this.props.resolve({ confirmed: false, payload: null });
    	     this.trigger('close-popup');
         }
	cancel() {
		debugger;
		this.props.resolve({ confirmed: false, payload: null });
        this.trigger('close-popup');
    	//this.destroy();
         }
	}

	CDFIDetailPopupWidget.template = 'CDFIDetailPopupWidget';


	CDFIDetailPopupWidget.defaultProps = {
		confirmText:'Confirmar',
		cancelText:'Cancelar',
		body:'',
		startingValue:'',
	};

	Registries.Component.add(CDFIDetailPopupWidget);

	return CDFIDetailPopupWidget;

});
