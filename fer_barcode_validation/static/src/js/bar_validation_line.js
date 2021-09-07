odoo.define('fer_barcode_validation.override_line', function(require) {
    'use strict';

    var NewWidget = require('stock_barcode.ClientAction')

    var core = require('web.core');

    var LinesWidget = require('stock_barcode.LinesWidget');

    var _t = core._t;

    var QWeb = core.qweb;
    NewWidget.include({

        _step_product: async function (barcode, linesActions) {
            var self = this;
            this.currentStep = 'product';
            this.stepState = $.extend(true, {}, this.currentState);
            var errorMessage;
            
            var provider = await this._getProvider();

            var product = await this._isProduct(barcode);
            if (product) {
                if (product.tracking !== 'none' && self.requireLotNumber) {
                    this.currentStep = 'lot';
                }
                var res = this._incrementLines({'product': product, 'barcode': barcode});
                if (res.isNewLine) {
                    if (this.actionParams.model === 'stock.inventory') {
                        // FIXME sle: add owner_id, prod_lot_id, owner_id, product_uom_id
                        return this._rpc({
                            model: 'product.product',
                            method: 'get_theoretical_quantity',
                            args: [
                                res.lineDescription.product_id.id,
                                res.lineDescription.location_id.id,
                            ],
                        }).then(function (theoretical_qty) {
                            res.lineDescription.theoretical_qty = theoretical_qty;
                            linesActions.push([self.linesWidget.addProduct, [res.lineDescription, self.actionParams.model]]);
                            self.scannedLines.push(res.id || res.virtualId);
                            return Promise.resolve({linesActions: linesActions});
                        });
                    } else {
                        linesActions.push([this.linesWidget.addProduct, [res.lineDescription, this.actionParams.model]]);
                    }
                } else if (!(res.id || res.virtualId)) {
                    return Promise.reject(_t("There are no lines to increment."));
                } else {
                    if (product.tracking === 'none' || !self.requireLotNumber) {
                        linesActions.push([this.linesWidget.incrementProduct, [res.id || res.virtualId, product.qty || 1, this.actionParams.model]]);
                    } else {
                        linesActions.push([this.linesWidget.incrementProduct, [res.id || res.virtualId, 0, this.actionParams.model]]);
                    }
                }
                this.scannedLines.push(res.id || res.virtualId);
                return Promise.resolve({linesActions: linesActions});
            } else {
                var success = function (res) {
                    return Promise.resolve({linesActions: res.linesActions});
                };
                var fail = function (specializedErrorMessage) {
                    self.currentStep = 'product';
                    if (specializedErrorMessage){
                        return Promise.reject(specializedErrorMessage);
                    }
                    if (! self.scannedLines.length) {
                        if (self.groups.group_tracking_lot) {
                            errorMessage = _t("You are expected to scan one or more products or a package available at the picking's location");
                        } else {
                            errorMessage = _t('You are expected to scan one or more products.');
                        }
                        return Promise.reject(errorMessage);
                    }
    
                    var destinationLocation = self.locationsByBarcode[barcode];
                    if (destinationLocation) {
                        return self._step_destination(barcode, linesActions);
                    } else {
                        errorMessage = _t('You are expected to scan more products or a destination location.');
                        return Promise.reject(errorMessage);
                    }
                };
                return self._step_lot(barcode, linesActions).then(success, function () {
                    return self._step_package(barcode, linesActions).then(success, fail);
                });
            }
        },
    
        _getProvider: function () {
            var self = this;
            console.dir(self.actionParams.id);
            return this._rpc({
                model: 'stock.picking',
                method: 'get_provider_cat',
                args: [self.actionParams.id],
            }).then(function (res) {
                self.providerCategory = res;
            });
        },
    
        _onAddLine: async function (ev) {
            var provider = await this._getProvider();
            
            if(this.providerCategory=="Mayorista"){
                alert("No se pueden agregar nuevas líneas de producto a este pedido.")
            }
            else{
                ev.stopPropagation();
                this.mutex.exec(() => {
                    this.linesWidgetState = this.linesWidget.getState();
                    this.linesWidget.destroy();
                    this.headerWidget.toggleDisplayContext('specialized');
                    // Get the default locations before calling save to not lose a newly created page.
                    var currentPage = this.pages[this.currentPageIndex];
                    var defaultValues = this._getAddLineDefaultValues(currentPage);
                    return this._save().then(() => {
                        this.ViewsWidget = this._instantiateViewsWidget(defaultValues);
                        return this.ViewsWidget.appendTo(this.$('.o_content'));
                    });
                });
            }
        },

        _incrementLines: function (params) {
            //alert("_incrementLines");
            console.log(params);
            var line = this._findCandidateLineToIncrement(params);
            var isNewLine = false;
            console.log(line);
            console.log(this);
            console.log(this.providerCategory);
            var provider=this.providerCategory;
            if (line) {
                // Update the line with the processed quantity.
                if (params.product.tracking === 'none' ||
                    params.lot_id ||
                    params.lot_name ||
                    !this.requireLotNumber
                    ) {
                    if (this._isPickingRelated()) {
                        //alert(provider);
                        if(provider == "Mayorista"){
                            if((line.qty_done+(params.product.qty || 1)) > line.product_uom_qty){
                                alert("La cantidad no puede ser mayor a la especificada en el pedido.");
                                // return Promise.reject(("La cantidad es mayor."));
                                return 0;
                            }
                            else{
                                line.qty_done += params.product.qty || 1;
                                if (params.package_id) {
                                    line.package_id = params.package_id;
                                }
                                if (params.result_package_id) {
                                    line.result_package_id = params.result_package_id;
                                }
                            }
                        }
                        else{
                            line.qty_done += params.product.qty || 1;
                            if (params.package_id) {
                                line.package_id = params.package_id;
                            }
                            if (params.result_package_id) {
                                line.result_package_id = params.result_package_id;
                            }
                        }
                    } else if (this.actionParams.model === 'stock.inventory') {
                        line.product_qty += params.product.qty || 1;
                    }
                }
            } else if (this._isAbleToCreateNewLine()) {
                if(provider=="Mayorista"){
                    alert("El producto no se puede agregar porque no se encuentra en el pedido.");
                    // return Promise.reject(("La cantidad es mayor."));
                    return 0;
                }
                else{
                    isNewLine = true;
                    // Create a line with the processed quantity.
                    if (params.product.tracking === 'none' ||
                        params.lot_id ||
                        params.lot_name ||
                        !this.requireLotNumber
                        ) {
                        params.qty_done = params.product.qty || 1;
                    } else {
                        params.qty_done = 0;
                    }
                    line = this._makeNewLine(params);
                    this._getLines(this.currentState).push(line);
                    this.pages[this.currentPageIndex].lines.push(line);
                }
            }
            if (this._isPickingRelated()) {
                if (params.lot_id) {
                    line.lot_id = [params.lot_id];
                }
                if (params.lot_name) {
                    line.lot_name = params.lot_name;
                }
            } else if (this.actionParams.model === 'stock.inventory') {
                if (params.lot_id) {
                    line.prod_lot_id = [params.lot_id, params.lot_name];
                }
            }
            return {
                'id': line.id,
                'virtualId': line.virtual_id,
                'lineDescription': line,
                'isNewLine': isNewLine,
            };
        },
        
   });
    
    return LinesWidget;
});