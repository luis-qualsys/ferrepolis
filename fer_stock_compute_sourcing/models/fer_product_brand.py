from odoo import api, fields, models


class FerProductBrand(models.Model):
    _name = 'fer.product.brand'
    _description = 'Marcas de productos'
    _rec_name = 'fer_brand_name'

    fer_brand_name = fields.Char(string='Nombre de marca', required=True)
    fer_brand_code = fields.Char(string='Código', required=True)
    product_id = fields.One2many('product.template', 'fer_brand_ids')
