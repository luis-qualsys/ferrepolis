from odoo import api, fields, models


class FerStockWarehouseOrderpointEfim(models.Model):
    _name = 'fer.stock.warehouse.orderpoint.efim'
    _description = 'Stock valores efimeros'

    product_id = fields.Many2one('product.product', string='Producto')
    # warehouse_id = fields.Many2one('stock.warehouse', string='Almacen')
    location_id = fields.Many2one('stock.location', string='Ubicación')
    fer_c_product_min = fields.Integer('Cal mínima', default=0)
    fer_c_product_max = fields.Integer('Cal máxima', default=0)
    fer_old_product_min = fields.Integer(string='Hist mínima', default=0, readonly=True)
    fer_old_product_max = fields.Integer(string='Hist máxima', default=0, readonly=True)
    fer_history_stock_orderpoint_ids = fields.Many2one('fer.history.stock.orderpoint', string="Historial de reglas abastecimiento")

    # Data saved
    fer_product_average = fields.Float(string='Valor promedio')
    fer_product_cumulative = fields.Float(string='Valor acumulado')
    fer_product_letter = fields.Char(string='Letra')
    fer_product_participation = fields.Float(string='Participación')
    fer_qty_done = fields.Float(string='Unidades vendidas')