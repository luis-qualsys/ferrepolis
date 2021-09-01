from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fer_brand_ids = fields.Many2one('fer.product.brand', string='Marca')