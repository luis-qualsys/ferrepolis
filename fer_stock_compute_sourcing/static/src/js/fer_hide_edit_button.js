odoo.define('fer_stock_compute_sourcing.fer_hide_edit_button.js', function (require) {

    const FormController = require('web.FormController');

    FormController.include({
        decideToShowButtons: function(){
            console.log('innerDecideToShowButtons')
            console.log('Decide This', this.modelName)
            if (this.modelName === "fer.history.stock.orderpoint"){
                // console.log('Model', this.modelName)
                console.log('Decide Model Local', this.model.localData)
                const dataModel = this.model.localData
                console.log(dataModel['fer.history.stock.orderpoint_1'].data.fer_state)
                if (dataModel['fer.history.stock.orderpoint_1'].data.fer_state !== 'draft'){
                    console.log('Hide button')
                    this.$buttons.find('.o_form_button_edit').hide()
                } else {
                    console.log('Show button')
                    this.$buttons.find('.o_form_button_edit').show()
                }
            }
        },
        renderButtons: function(){
            // console.log('render buttons');
            this._super.apply(this, arguments);
            this.decideToShowButtons();
        },
        reload: function(){
            var self = this;
            // console.log('reload record');
            return this._super.apply(this, arguments).then(function(res){
                self.decideToShowButtons();
                return res;
            });
        },
        saveRecord: function() {
            // console.log('save record');
            var self = this;
            return this._super.apply(this, arguments).then(function(res){
                self.decideToShowButtons();
                return res;
            })
        }
    });
});