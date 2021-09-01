# -*- coding = utf - 8 -*-
import logging
_logger = logging.getLogger(__name__)

from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError

class LogInvoiceLine(models.Model): 
    _name = "log.invoice.line"
    _description = "Historial de diferencias en líneas de factura XML y solicitudes de presupuesto."
    _order = "id"

    fer_product_id= fields.Many2one("product.product",string="Producto")
    fer_po_id = fields.Many2one("purchase.order",string="Orden de compra")
    fer_qty_original = fields.Float(string="Cantidad solicitada")
    fer_qty_received = fields.Float(string="Cantidad actualizada")
    fer_qty_diff = fields.Float(string="Diferencia")
    fer_price_original = fields.Float(string="Precio Original")
    fer_price_new = fields.Float(string="Precio Unitario")
    fer_tax_original = fields.Float(string="IVA Original")
    fer_tax_new = fields.Many2many("account.tax",string="IVA")
