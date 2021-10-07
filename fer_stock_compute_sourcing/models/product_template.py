from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fer_brand_ids = fields.Many2one('fer.product.brand', string='Marca')

class StockLocation(models.Model):
    _inherit = 'stock.location'

    fer_search_location = fields.One2many('fer.stock.computer.parms', 'location_ids', string='Parametros de abastecimiento')
    fer_search_flag = fields.Boolean(string='Usar en calculo de stock', default=False, compute='_get_search_flag', store=True)

    @api.depends('fer_search_location')
    def _get_search_flag(self):
        for record in self:
            if record.fer_search_location:
                record.fer_search_flag = True
            else:
                record.fer_search_flag = False