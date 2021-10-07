from odoo import _, models, fields, api
from odoo.exceptions import ValidationError, AccessError, UserError

class FerHistoryStockOrderpoint(models.Model):
    _name = "fer.history.stock.orderpoint"
    _description = "Historial de abastecimiento"
    _rec_name = 'fer_name'
    _order = 'fer_name desc'

    fer_name = fields.Char(string='Nombre', compute='_fer_get_name', store=True)
    fer_timestamp = fields.Datetime(string='Fecha de cálculo', default=lambda date: fields.Datetime.now(), required=True, readonly=True)
    # fer_description = fields.Char(string="Descripción del cálculo")
    fer_stock_rules_efim_ids = fields.One2many('fer.stock.warehouse.orderpoint.efim', 'fer_history_stock_orderpoint_ids', string="Historial de reglas abastecimiento")
    fer_state = fields.Selection(string='Estado', default='draft',
            selection=[
                ('draft', 'Borrador'),
                ('applied', 'Aplicado'),
                ('restored', 'Restaurado'),
                ('cancelled', 'Cancelado')
                ])
    location_id = fields.Char(string='Ubicación', readonly=True)
    fer_date_init = fields.Date(string='Fecha de inicio', readonly=True)
    fer_date_end = fields.Date(string='Fecha de termino', readonly=True)
    fer_brand = fields.Char(string='Marca', readonly=True)
    fer_prod_init = fields.Char(string='Producto inicial', readonly=True)
    fer_prod_end = fields.Char(string='Producto final', readonly=True)
    fer_origin = fields.Selection(string='Origen', default='stock',
            selection=[
                ('stock', 'Cálculo de Stock'),
                ('stock_week', 'Cálculo de Stock por Semanas')
                ], readonly=True)

    @api.depends('fer_timestamp')
    def _fer_get_name(self):
        for record in self:
            record.fer_name = '%s - [%s]' % (record.id, record.fer_timestamp)

    def action_calculed_recover(self):
        self.ensure_one()
        # Borrar reglas anteriores
        rules_actived = self.env['stock.warehouse.orderpoint'].search([])

        products_ids_actived = [rule.product_id.id for rule in rules_actived]
        locations_ids_actived = [rule.location_id.id for rule in rules_actived]

        for rule in self.fer_stock_rules_efim_ids:
            if rule.product_id.id in products_ids_actived and rule.location_id.id in locations_ids_actived:
                old_rule = self.env['stock.warehouse.orderpoint'].search([
                    ('product_id.id', '=', rule.product_id.id), 
                    ('location_id.id', '=', rule.location_id.id)]
                    )
                if old_rule:
                    old_rule.write({
                        'product_min_qty': rule.fer_c_product_min,
                        'product_max_qty': rule.fer_c_product_max
                        })
                else:
                    old_rule = self.env['stock.warehouse.orderpoint'].search([]).create([{
                        'product_id': rule.product_id.id,
                        'location_id': rule.location_id.id,
                        'product_min_qty': rule.fer_c_product_min,
                        'product_max_qty': rule.fer_c_product_max,
                        'qty_multiple': 1,
                        'trigger': 'auto'
                        }])
                
                continue
            else:
                old_rule = self.env['stock.warehouse.orderpoint'].search([]).create([{
                    'product_id': rule.product_id.id,
                    'location_id': rule.location_id.id,
                    'product_min_qty': rule.fer_c_product_min,
                    'product_max_qty': rule.fer_c_product_max,
                    'qty_multiple': 1,
                    'trigger': 'auto'
                        }])

        self.fer_state = 'applied'
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_hist_recover(self):
        self.ensure_one()
        # Borrar reglas anteriores
        rules_actived = self.env['stock.warehouse.orderpoint'].search([])

        products_ids_actived = [rule.product_id.id for rule in rules_actived]
        locations_ids_actived = [rule.location_id.id for rule in rules_actived]

        for rule in self.fer_stock_rules_efim_ids:
            if rule.product_id.id in products_ids_actived and rule.location_id.id in locations_ids_actived:
                old_rule = self.env['stock.warehouse.orderpoint'].search([
                    ('product_id.id', '=', rule.product_id.id), 
                    ('location_id.id', '=', rule.location_id.id)]
                    )
                if old_rule:
                    old_rule.write({
                        'product_min_qty': rule.fer_old_product_min,
                        'product_max_qty': rule.fer_old_product_max
                        })
                else:
                    old_rule = self.env['stock.warehouse.orderpoint'].search([]).create([{
                        'product_id': rule.product_id.id,
                        'location_id': rule.location_id.id,
                        'product_min_qty': rule.fer_old_product_min,
                        'product_max_qty': rule.fer_old_product_max,
                        'qty_multiple': 1,
                        'trigger': 'auto'
                        }])
                continue
            else:
                old_rule = self.env['stock.warehouse.orderpoint'].search([]).create([{
                    'product_id': rule.product_id.id,
                    'location_id': rule.location_id.id,
                    'product_min_qty': rule.fer_old_product_min,
                    'product_max_qty': rule.fer_old_product_max,
                    'qty_multiple': 1,
                    'trigger': 'auto'
                        }])
        self.fer_state = 'restored'
        return {'type': 'ir.actions.client', 'tag': 'reload'}
    
    def action_draft_state(self):
        self.ensure_one()
        self.fer_state = 'draft'
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_cancel_compute(self):
        self.fer_state = 'cancelled'
        return {'type': 'ir.actions.client', 'tag': 'reload'}
