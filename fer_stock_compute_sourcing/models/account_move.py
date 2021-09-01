from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'
    fer_sourcing_ids = fields.Many2one('fer.compute.model.search')
