odoo.define('pos_create_so_offline', function (require) {
"use strict";

    const models = require('point_of_sale.models');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const PosComponent = require('point_of_sale.PosComponent');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const PosDB = require('point_of_sale.DB');
    const { useState, useRef } = owl.hooks;
    const { posbus } = require('point_of_sale.utils');


    class SaleSynchNotificationWidget extends PosComponent {
        constructor() {
            super(...arguments);
            const synch = this.env.pos.get('sosynch');
            this.state = useState({ status: synch.status, msg: synch.pending });
        }
        mounted() {
            this.env.pos.on(
                'change:sosynch',
                (pos, synch) => {
                    this.state.status = synch.status;
                    this.state.msg = synch.pending;
                },
                this
            );
        }
        willUnmount() {
            this.env.pos.on('change:sosynch', null, this);
        }
        onClick() {
            this.env.pos.push_sale_order(null, { show_error: true });
        }
    }
    SaleSynchNotificationWidget.template = 'SaleSynchNotificationWidget';
    Registries.Component.add(SaleSynchNotificationWidget);

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function() {
            _super_order.initialize.apply(this,arguments);
            this.wv_note = "";
            this.order_ref = "";
            this.save_to_db();
        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this,arguments);
            json.wv_note = this.wv_note;
            return json;
        },
        export_for_printing:function() {
            var json = _super_order.export_for_printing.apply(this,arguments);
            json.wv_note = this.wv_note;
            json.order_ref = this.order_ref;
            return json
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this,arguments);
            this.wv_note = json.wv_note;
            this.order_ref = json.order_ref;
        },
    });

    class CreateSaleOrderButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        async onClick() {
            var self = this;
            await this.showPopup('CreateSaleOrderPopupWidget');
            
        }
        
    }
    CreateSaleOrderButton.template = 'CreateSaleOrderButton';

    ProductScreen.addControlButton({
        component: CreateSaleOrderButton,
        condition: function() {
            return this.env.pos.config.allow_create_sale_order;
        },
    });

    Registries.Component.add(CreateSaleOrderButton);


    class CreateSaleOrderPopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({ inputValue: this.props.startingValue });
            this.inputRef = useRef('input');
            this.changes = {};
        }

        getPayload() {
            return this.state.inputValue;
        }

        async captureChange(event) {
            var order =this.env.pos.get('selectedOrder');
            if(order.get_client() != null){
                order.wv_note = $(".wv_note").val();
                await this.save_order();
                await this.trigger('close-popup');
            }
            else{
             alert("De verdad no vas a seleccionar el cliente ? !!!!");
            }
        }

        async print_quotation_bill(event) {
            var order =this.env.pos.get('selectedOrder');
            if(order.get_client() != null){
                order.wv_note = $(".wv_note").val();
                var data = order.export_as_JSON();
                this.env.pos.push_sale_order(data);
                await this.trigger('close-popup');
                await this.showTempScreen('SaleOrderBillScreenWidget');


            }
            else{
             alert("De Verdad ? pedido sin cliente ?? !!!!");
            }
            // this.cancel();
        }
        save_order(){
            var self = this;
            var order = self.env.pos.get_order();
            var data = order.export_as_JSON();
            self.env.pos.push_sale_order(data);
            if(order){
                order.destroy({'reason': 'abandon'});
                posbus.trigger('order-deleted');
                self.env.pos.trigger('change:selectedOrder', self.env.pos, self.env.pos.get_order());
            }
        }
    }
    CreateSaleOrderPopupWidget.template = 'CreateSaleOrderPopupWidget';
    Registries.Component.add(CreateSaleOrderPopupWidget);
    CreateSaleOrderPopupWidget.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancelar',
        title: 'Detalles del pedido',
        body: '',
    };

    const SaleOrderBillScreenWidget = (ReceiptScreen) => {
        class SaleOrderBillScreenWidget extends ReceiptScreen {
            mounted() {
            }
            confirm() {
                var self =  this;
                var order = this.env.pos.get_order();
                if(order){
                    order.destroy({'reason': 'abandon'});
                    posbus.trigger('order-deleted');
                    self.env.pos.trigger('change:selectedOrder', self.env.pos, self.env.pos.get_order());
                }
                this.props.resolve({ confirmed: true, payload: null });
                this.trigger('close-temp-screen');
            }
        }
        SaleOrderBillScreenWidget.template = 'SaleOrderBillScreenWidget';
        return SaleOrderBillScreenWidget;
    };

    Registries.Component.addByExtending(SaleOrderBillScreenWidget, ReceiptScreen);

    PosDB.include({
        add_sale_order: function(order){
            var order_id = order.uid;
            var orders  = this.load('sale_orders',[]);
            for(var i = 0, len = orders.length; i < len; i++){
                if(orders[i].id === order_id){
                    orders[i].data = order;
                    this.save('sale_orders',orders);
                    return order_id;
                }
            }
            orders.push({id: order_id, data: order});
            this.save('sale_orders',orders);
            return order_id;
        },
        get_sale_orders: function(){

            return this.load('sale_orders',[]);
        },
        get_sale_order: function(order_id){
            var orders = this.get_sale_orders();
            for(var i = 0, len = orders.length; i < len; i++){
                if(orders[i].id === order_id){
                    return orders[i];
                }
            }
            return undefined;
        },
        remove_sale_order: function(order_id){
            var orders = this.load('sale_orders',[]);
            orders = _.filter(orders, function(order){
                return order.id !== order_id;
            });
            this.save('sale_orders',orders);
        },
        remove_partner: function(partner_id){
            var orders = this.load('orders',[]);
            orders = _.filter(orders, function(order){
                return order.id !== order_id;
            });
            this.save('orders',orders);
        },
    });
    var _super_PosModel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function(attributes) {
            this.set({'sosynch' :{ status:'connected', pending:0 }});
            return _super_PosModel.initialize.apply(this,arguments);
        },
        _flush_sale_orders: function(orders, options) {
            var self = this;
            this.set('sosynch',{ status: 'connecting', pending: orders.length});
            return self._save_to_server_cust(orders, options).then(function (server_ids) {
                var pending = self.db.get_sale_orders().length;

                self.set('sosynch', {
                    status: pending ? 'connecting' : 'connected',
                    pending: pending
                });

                return server_ids;
            }).catch(function(error){
                var pending = self.db.get_sale_orders().length;
                if (self.get('failed')) {
                    self.set('sosynch', { status: 'error', pending: pending });
                } else {
                    self.set('sosynch', { status: 'disconnected', pending: pending });
                }
            });
        },
    _save_to_server_cust: function (orders, options) {
        if (!orders || !orders.length) {
            return Promise.resolve([]);
        }
        options = options || {};
        var self = this;
        var timeout = typeof options.timeout === 'number' ? options.timeout : 30000 * orders.length;
        var order_ids_to_sync = _.pluck(orders, 'id');
        return this.rpc({
                model: 'sale.order',
                method: 'create_new_quotation',
                args: [orders],
                kwargs: {context: this.session.user_context},
            }, {
                timeout: timeout,
                shadow: !options.to_invoice
            })
            .then(function (server_ids) {
                _.each(order_ids_to_sync, function (order_id) {
                    self.db.remove_sale_order(order_id);
                });

                self.set('failed',false);
                return server_ids;
            }).catch(function (reason){
                var error = reason.message;
                console.warn('Failed to send orders:', orders);
                if(error.code === 200 ){    // Business Logic Error, not a connection problem
                    // Hide error if already shown before ...
                    if ((!self.get('failed') || options.show_error) && !options.to_invoice) {
                        self.set('failed',error);
                        throw error;
                    }
                }
                throw error;
            });
    },

        push_sale_order: function(sale_order, opts) {
            opts = opts || {};
            var self = this;
            if(sale_order){
                this.db.add_sale_order(sale_order);
            }
            return new Promise(function (resolve, reject) {
                self.flush_mutex.exec(function () {
                    var flushed = self._flush_sale_orders(self.db.get_sale_orders(), opts);

                    flushed.then(resolve, reject);

                    return flushed;
                });
            });
        },
    }); 
});
