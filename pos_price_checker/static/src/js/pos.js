odoo.define('pos_price_checker', function (require) {
"use strict";

    const { debounce } = owl.utils;
    const PosComponent = require('point_of_sale.PosComponent');
    const { useState, useRef } = owl.hooks;
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const Chrome = require('point_of_sale.Chrome');
    var devices = require('point_of_sale.BarcodeReader');
    const { posbus } = require('point_of_sale.utils');
    const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');

    class PriceCheckerScreen extends PosComponent {
        constructor() {
            super(...arguments);
            var self = this;
            useBarcodeReader({
                product: this._barcodeProductAction,
                weight: this._barcodeProductAction,
                price: this._barcodeProductAction,
            })
            var products = this.env.pos.db.product_by_id;
            var availableTags = [];
            $.each( products, function( i, val ) {
              availableTags.push({id:val.id,value:val.display_name});
            });

            setTimeout(function(){ 
                $('.screen-content-searchbox input').autocomplete({
                    source: availableTags,
                    select: function (event, ui) {
                        if(ui != undefined){
                            setTimeout(function(){ 
                                $('.screen-content-searchbox input').val("");
                            }, 30);
                            var product = self.env.pos.db.product_by_id[ui.item.id];
                            self.props.product = product;
                            self.render();
                        }
                    }
                });
                }, 30);
        }
        _barcodeProductAction(code) {
           var product = this.env.pos.db.product_by_barcode[code.code];
           this.props.product = product;
           this.render();
        }
 
    }
    PriceCheckerScreen.template = 'PriceCheckerScreen';
    PriceCheckerScreen.hideOrderSelector = true;

    Registries.Component.add(PriceCheckerScreen);

    const PosResChrome = (Chrome) =>
        class extends Chrome {
            get startScreen() {

                if(this.env.pos.config.allow_price_checker){
                    return { name: 'PriceCheckerScreen',props: {'pos':this.env.pos}}
                }
                else{
                    return super.startScreen;
                }
            }
        }

    Registries.Component.extend(Chrome, PosResChrome);
});

