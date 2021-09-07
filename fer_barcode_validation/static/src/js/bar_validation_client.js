odoo.define('fer_barcode_validation.override_widget', function(require) {
    'use strict';

    var NewWidget = require('stock_barcode.ViewsWidget')

    NewWidget.include({
        _getProvider: function (id) {
            var self = this;
            // console.dir(self.actionParams.id);
            return this._rpc({
                model: 'stock.picking',
                method: 'get_provider_cat',
                args: [id],
            }).then(function (res) {
                self.providerCategory = res;
            });
        },
        _onClickSave: async function (ev) {
            ev.stopPropagation();
            var self = this;
            //console.dir(self);
            var record1 = self.controller.model.get(self.controller.handle);
            console.dir(record1.data.picking_id.res_id);
            var qty_done=record1.data.qty_done;
            var qty_total=record1.data.product_uom_qty;
            console.dir(record1.data);
            var provider = await this._getProvider(record1.data.picking_id.res_id);
            console.log(this.providerCategory);

            if(this.providerCategory=="Mayorista"){
                if(qty_done > qty_total){
                    alert("No se puede asignar una cantidad mayor a la pedida.")
                }
                else{
                    var def = this.controller.saveRecord(this.controller.handle, {stayInEdit: true, reload: false});
                    def.then(function () {
                        var record = self.controller.model.get(self.controller.handle);
                        self.trigger_up('reload', {'record': record});
                    });
                }
            }
            else{
                var def = this.controller.saveRecord(this.controller.handle, {stayInEdit: true, reload: false});
                def.then(function () {
                    var record = self.controller.model.get(self.controller.handle);
                    self.trigger_up('reload', {'record': record});
                });
            }
        },
        
    });
    return NewWidget;
    
    });
    