from odoo import api, fields, models
from dateutil.relativedelta import relativedelta

class FerComputeModelSearch(models.Model):
    _name = 'fer.compute.model.search'
    _description = 'Modelo de busqueda para calculos'

    # Data for compute
    fer_product_id_init = fields.Integer(string='Producto inicial')
    fer_product_id_end = fields.Integer(string='Producto final')
    warehouse_id = fields.Many2one('stock.warehouse', string='Almacen')
    location_id = fields.Many2one('stock.location', string='Ubicación', required=True)
    fer_brand = fields.Many2one('fer.product.brand', string='Marca')
    fer_date_init = fields.Date(string='Periodo de inicio', required=True, default=lambda date: fields.Date.today() - relativedelta(days=10))
    fer_date_end = fields.Date(string='Periodo de termino', default=lambda date: fields.Date.today(), required=True)
    partner_id = fields.Many2many('res.partner', string='Clientes')
    account_ids = fields.Many2many('account.move', string='Facturas')
    fer_omit_days = fields.Integer(string='No. dias a omitir', default=0)
    fer_check_partner = fields.Boolean(string='Omitir clientes', default=False)
    fer_check_invoice = fields.Boolean(string='Omitir facturas', default=False)
    fer_check_selector = fields.Selection(string='Omitir', 
        selection=[
            ('no', 'Ninguno'),
            ('invoices', 'Facturas'),
            ('partners', 'Clientes')],
        default="no")

    # Computed fields
    fer_timelapse = fields.Integer(string='Días', readonly=True, compute='_fer_compute_days_timelapse')
    fer_range_ids = fields.Integer(string='Rango de productos', readonly=True, compute='_fer_compute_range_ids')

    @api.onchange('fer_date_init', 'fer_date_end')
    def _fer_compute_days_timelapse(self):
        for record in self:
            if record.fer_date_end and record.fer_date_init:
                timelapse = record.fer_date_end - record.fer_date_init
                record.fer_timelapse = timelapse.days
            else:
                record.fer_timelapse = 1
                

    @api.onchange('fer_product_id_init', 'fer_product_id_end')
    def _fer_compute_range_ids(self):
        for record in self:
            if record.fer_product_id_init and record.fer_product_id_end:
                record.fer_range_ids = record.fer_product_id_end - record.fer_product_id_init
            else:
                record.fer_range_ids = 1

    