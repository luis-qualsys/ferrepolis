from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'
    fer_sourcing_ids = fields.Many2one('fer.compute.model.search')