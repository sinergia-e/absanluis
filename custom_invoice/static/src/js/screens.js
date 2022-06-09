odoo.define('custom_invoice.screens', function (require) {
	"use strict";

var core = require('web.core');
var screens = require('point_of_sale.screens');
var rpc    = require('web.rpc');

var QWeb = core.qweb;
var _t = core._t;

screens.ReceiptScreenWidget.include({
    render_receipt: function() {
    debugger;
        var self = this;
        var order = this.pos.get_order();
        
        var order_lines = order.get_orderlines();
        var receipt_language = order.receipt_language;
        
        /*if(order.is_to_invoice()){*/
        	//new Model('pos.order').call('get_invoice_information',[order.get_name()])
    	
    	
    	
    	this.get_invoice_data = rpc.query({
            model: 'pos.order',
            method: 'get_invoice_information',
            args: [order.get_name()],
        }).then(function(res){
        	var template = 'PosTicketCFDIWithoutInvoice';
        	if (order.is_to_invoice()){
        		template = 'PosTicketCFDI';
        	}
        	
            $('.pos-receipt-container').html(QWeb.render(template,{
                widget:self,
                order: order,
                receipt: order.export_for_printing(),
                orderlines: order.get_orderlines(),
                paymentlines: order.get_paymentlines(),
                methodo_pago : res.methodo_pago,
                regimen_fiscal_id : res.regimen_fiscal_id,
                forma_pago_id : res.forma_pago_id,
                numero_cetificado : res.numero_cetificado,
                moneda : res.moneda,
                cetificaso_sat : res.cetificaso_sat,
                tipocambio : res.tipocambio,
                folio_fiscal : res.folio_fiscal,
                fecha_certificacion : res.fecha_certificacion,
                cadena_origenal : res.cadena_origenal,
                selo_digital_cdfi : res.selo_digital_cdfi,
                selo_sat : res.selo_sat,
                invoice_id : res.invoice_id,
                tipo_comprobante : res.tipo_comprobante,
                invoice_date : res.invoice_date,
                folio_factura : res.folio_factura,
                uso_cfdi_id : res.uso_cfdi_id,
                client_name : res.client_name,
                client_rfc : res.client_rfc,
            }));
            
        },function(err,event){
            event.preventDefault();
            self.gui.show_popup('error',{
                'title': _t('Error'),
                'body': _t('Your Internet connection is probably down.'),
            });
        });
        /*}
        else{
        	this._super();
        }*/
        
    },
    print_web: function(){
    	var self = this;
    	if (this.get_invoice_data){
    		$.when(this.get_invoice_data).always(function() {
    			window.print();
    	        self.pos.get_order()._printed = true;
        	});
    	}
    	else{
    		this._super();
    	}
    },
});

screens.PaymentScreenWidget.include({

    // Check if the order is paid, then sends it to the backend,
    // and complete the sale process
    validate_order: function(force_validation) {
        var self = this;
        if(this.pos.config.enable_order_note) {
            var currentOrder = this.pos.get_order();
            currentOrder.set_order_note($('#order_note').val());
        }

        var order = this.pos.get_order();

        // FIXME: this check is there because the backend is unable to
        // process empty orders. This is not the right place to fix it.
        if (order.get_orderlines().length === 0) {
            this.gui.show_popup('error',{
                'title': _t('Empty Order'),
                'body':  _t('There must be at least one product in your order before it can be validated'),
            });
            return;
        }

        // get rid of payment lines with an amount of 0, because
        // since accounting v9 we cannot have bank statement lines
        // with an amount of 0
        order.clean_empty_paymentlines();

        var plines = order.get_paymentlines();
        for (var i = 0; i < plines.length; i++) {
			// alert(plines[i].get_payment_status() === 'bank');
            if (plines[i].get_payment_status() === 'bank' && plines[i].get_amount() < 0) {
                this.pos_widget.screen_selector.show_popup('error',{
                    'message': _t('Negative Bank Payment'),
                    'comment': _t('You cannot have a negative amount in a Bank payment. Use a cash payment method to return money to the customer.'),
                });
                return;
            }
        }

        if (!order.is_paid() || this.invoicing) {
            return;
        }

        // The exact amount must be paid if there is no cash payment method defined.
        if (Math.abs(order.get_total_with_tax() - order.get_total_paid()) > 0.00001) {
            var cash = false;
            
            for (var i = 0; i < this.pos.payment_methods.length; i++) {
                cash = cash || (this.pos.payment_methods[i].is_cash_count);
            }
            if (!cash) {
                this.gui.show_popup('error',{
                    title: _t('Cannot return change without a cash payment method'),
                    body:  _t('There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration'),
                });
                return;
            }
        }

        // if the change is too large, it's probably an input error, make the user confirm.
        if (!force_validation && (order.get_total_with_tax() * 1000 < order.get_total_paid())) {
            this.gui.show_popup('confirm',{
                title: _t('Please Confirm Large Amount'),
                body:  _t('Are you sure that the customer wants to  pay') + 
                       ' ' + 
                       this.format_currency(order.get_total_paid()) +
                       ' ' +
                       _t('for an order of') +
                       ' ' +
                       this.format_currency(order.get_total_with_tax()) +
                       ' ' +
                       _t('? Clicking "Confirm" will validate the payment.'),
                confirm: function() {
                    self.validate_order('confirm');
                },
            });
            return;
        }

        if (order.is_paid_with_cash() && this.pos.config.iface_cashdrawer) { 

                this.pos.proxy.open_cashbox();
        }

        if (order.is_to_invoice()) {
            var invoiced = this.pos.push_and_invoice_order(order);
            this.invoicing = true;

            invoiced.fail(function(error){
                self.invoicing = false;
                if (error.message === 'Missing Customer') {
                    self.gui.show_popup('confirm',{
                        'title': _t('Please select the Customer'),
                        'body': _t('You need to select the customer before you can invoice an order.'),
                        confirm: function(){
                            self.gui.show_screen('clientlist');
                        },
                    });
                } else if (error.code < 0) {        // XmlHttpRequest Errors
                    self.gui.show_popup('error',{
                        'title': _t('The order could not be sent'),
                        'body': _t('Check your internet connection and try again.'),
                    });
                } else if (error.code === 200) {    // OpenERP Server Errors
                    self.gui.show_popup('error-traceback',{
                        'title': error.data.message || _t("Server Error"),
                        'body': error.data.debug || _t('The server encountered an error while receiving your order.'),
                    });
                } else {                            // ???
                    self.gui.show_popup('error',{
                        'title': _t("Unknown Error"),
                        'body':  _t("The order could not be sent to the server due to an unknown error"),
                    });
                }
            });
			
            invoiced.done(function(){
                self.invoicing = false;
                // order.finalize();
        	    self.gui.show_screen('receipt');
            });
        } else {
            this.pos.push_order(order);
            this.gui.show_screen('receipt');
        }
    },
    render_pago: function() {
        var self = this;
        var pago = $(QWeb.render('CDFIDetailPopupWidget', { widget:this }));
        pago.on('click','confirm',function(){
            alert('Confirm');
        });
        return pago;
    },
    click_invoice: function(){
   
    	var self = this;

        //var pago = $(QWeb.render('CDFIDetailPopupWidget', { widget:this }));
        //this.$('.detalles_pago').html(QWeb.render('CDFIDetailPopupWidget'));
        
        var order = this.pos.get_order();
        order.set_to_invoice(!order.is_to_invoice());
        if (order.is_to_invoice()) {
        	var pago = self.render_pago();
        	pago.appendTo(this.$('.detalles_pago'));
            this.$('.confirm').click(function(){
            	var forma_pago = $( ".js_forma_pago").val();
                	order.set_forma_pago(forma_pago);
                	
                	var methodo_pago = $( ".js_methodo_pago").val();
                	order.set_methodo_pago(methodo_pago);

                	var uso_cfdi = $( ".js_uso_cfdi").val();
                	order.set_uso_cfdi(uso_cfdi);

                pago.hide();
            });
            this.$('.cancel').click(function(){
            	pago.hide();
            });
            
            this.$('.js_invoice').addClass('highlight');
        } else {
            this.$('.js_invoice').removeClass('highlight');
        }
    },
	renderElement: function() {
        var self = this;
        this._super();

        this.$('.js_representative').change(function(){
        	var representative_id = $( ".js_representative").val();
        	self.select_representative(representative_id);
        });
	},
});

screens.ClientListScreenWidget.include({
	save_client_details: function(partner) {
        var self = this;
		        
        var fields = {};
        this.$('.client-details-contents .detail').each(function(idx,el){
            fields[el.name] = el.value;
        });

        if (!fields.name) {
            this.gui.show_popup('error',_t('A Customer Name Is Required'));
            return;
        }
        
        if (this.uploaded_picture) {
            fields.image = this.uploaded_picture;
        }

        fields.id           = partner.id || false;
        fields.country_id   = fields.country_id || false;
        fields.barcode      = fields.barcode || '';
        fields.is_company   = true;

        rpc.query({
            model: 'res.partner',
            method: 'create_from_ui',
            args: [fields],
        }).then(function(partner_id){
            self.saved_client_details(partner_id);
        },function(err,event){
            event.preventDefault();
            self.gui.show_popup('error',{
                'title': _t('Error: Could not Save Changes'),
                'body': _t('Your Internet connection is probably down.'),
            });
        });
    },
})

});
