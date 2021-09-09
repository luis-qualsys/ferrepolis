from odoo import api, fields, models


class FerStockComputerParms(models.Model):
    _name = 'fer.stock.computer.parms'
    _description = 'Parametros para cálculos de reabastecimiento de stock'
    _rec_name = 'fer_table_name'


    fer_table_name = fields.Char(compute='_fer_compute_get_name', string="Nombre")
    fer_letters_id = fields.One2many('fer.letters','fer_stock_computer_parm_ids', 'Letras')

    @api.depends()
    def _fer_compute_get_name(self):
        for table in self:
            table.fer_table_name = 'Parámetros de stock'

class ferLetters(models.Model):
    _name = 'fer.letters'
    _description = 'Parametros para los tipos de letras'

    fer_letter = fields.Char(string='Letra')
    fer_percent = fields.Integer(string='Valor %')
    fer_days_min_stock = fields.Integer(string='Días mínimos de Stock')
    fer_days_max_stock = fields.Integer(string='Días máximos de Stock')
    fer_stock_computer_parm_ids = fields.Many2one('fer.stock.computer.parms')