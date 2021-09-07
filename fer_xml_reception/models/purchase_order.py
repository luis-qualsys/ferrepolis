from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError
from lxml import etree
import base64

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model): 
    _inherit = "purchase.order"

    fer_supplier_invoices = fields.One2many('fer.supplier.invoice', 'fer_purchase_order_id', string="Facturas CFDI")
    fer_log_invoice_lines = fields.One2many('log.invoice.line', 'fer_po_id', string="Historial de líneas")
    fer_invoice = fields.Char(string='Factura')    
    fer_category = fields.Char(string='Categoría',compute='_compute_total')
    fer_txt = fields.Binary(string='Archivo txt')

    @api.depends('partner_id')
    def _compute_total(self):
        logging.info("############################### computed self: %s",self)
        flag=0
        for cat in self.partner_id.category_id:
            if cat.name == 'Mayorista':
                flag=1
        if flag==0:
            self.fer_category='otro'
        else:
            self.fer_category='Mayorista'

    def button_cancel(self):
        res = super(PurchaseOrder, self).button_cancel()
        for invoice in self.fer_supplier_invoices:
            invoice.unlink()
        return res

    def button_validate(self):
        res = super(PurchaseOrder, self).button_validate()
        
        return res

    def button_confirm(self):
        if self.partner_id.category_id.name == "Mayorista":
            if self.fer_invoice == False:
                raise ValidationError("No se ha agregado la factura XML.")

            ## Hacer cambios en cantidades y productos conforme a las diferencias si se confirma el pedido
            for log_line in self.fer_log_invoice_lines:
                flag=0
                for po_line in self.order_line:
                    if log_line.fer_product_id==po_line.product_id:
                        flag=1
                        if log_line.fer_qty_received==0:
                            logging.info("############################### Se elimina la linea de PO: %s",po_line)
                            po_line.unlink()
                        else:
                            logging.info("############################### Se cambia la cantidad a %s en: %s",log_line.fer_qty_received,po_line)
                            po_line.product_qty=log_line.fer_qty_received
                            po_line.price_unit=log_line.fer_price_new
                            po_line.taxes_id=log_line.fer_tax_new
                if flag==0:
                    logging.info("############################### Crear nueva PO: %s",log_line)
                    vals={
                        'product_id': log_line.fer_product_id.id,
                        'name': log_line.fer_product_id.name,
                        'product_qty': log_line.fer_qty_received,
                        'price_unit': log_line.fer_price_new,
                        'taxes_id': log_line.fer_tax_new,
                        'order_id' : self.id,
                    }
                    self.order_line.create(vals)

        res = super(PurchaseOrder, self).button_confirm()
        return res

    def delete_xml(self):
        logging.info("############################### delete: %s",self.fer_invoice)
        self.fer_invoice = None
        self.partner_ref = None
        logging.info("############################### Si cambiaron, revertir líneas de PO.")
        for log_line in self.fer_log_invoice_lines:
            flag=0
            for po_line in self.order_line:
                if po_line.product_id==log_line.fer_product_id:
                    flag=1
                    if log_line.fer_qty_original == 0:
                        logging.info("############################### Borrar línea de PO %s",po_line.product_id.default_code)
                        po_line.unlink()
                    else:
                        logging.info("############################### Actualizar cantidad, precio, iva:  %s",po_line.product_id.default_code)
                        po_line.product_qty = log_line.fer_qty_original
                        po_line.price_unit = log_line.fer_price_original
                        original_tax = self.env['account.tax'].search([('amount','=',log_line.fer_tax_original),('type_tax_use','=','purchase')])
                        po_line.taxes_id = original_tax
            if flag==0 and log_line.fer_qty_original > 0:
                logging.info("############################### Crear línea en PO %s",log_line.fer_product_id.default_code)
                vals={
                    'product_id': log_line.fer_product_id.id,
                    'name': log_line.fer_product_id.name,
                    'product_qty': log_line.fer_qty_original,
                    'order_id' : self.id,
                }
                self.order_line.create(vals)


        logging.info("############################### Borrar todas las líneas de pestaña.")
        for log_line in self.fer_log_invoice_lines:
            log_line.unlink()

        supplier_lines = self.env['fer.supplier.invoice'].search([('fer_purchase_order_id','=',self.id)])
        for line in supplier_lines:
            line.unlink()


    def download_txt(self):
        self.state='sent'
        nombre="Solicitud"+self.name+".txt"
        ruta ="/odoo14hd/odoo14hd-server/Odoo_14hd/" + nombre
        # ruta ="/odoo/odoo-server/" + nombre
        data = open(ruta,'w+')
        data.write("%s \r\n" % self.partner_id.ref)
        for line in self.order_line:
            data.write("%s,%d\r\n" % (line.product_id.default_code,int(line.product_qty)))
        file_data = data.read()
        data.close()
        self.fer_txt = base64.b64encode(open(ruta, "rb").read())
        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': '/web/content/purchase.order/%s/fer_txt/%s?download=true' %(self.id,nombre),
        }
    # def download_txt(self):
    #     self.state='sent'
    #     nombre="Solicitud de presupuesto - "+self.name+".txt"
    #     data = open(nombre,'w+')
    #     data.write("%s \r\n" % self.partner_id.ref)
    #     for line in self.order_line:
    #         data.write("%s,%d\r\n" % (line.product_id.default_code,int(line.product_qty)))
    #     file_data = data.read()
    #     data.close()
    #     self.fer_txt = base64.b64encode(open(nombre, "rb").read())
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'name': 'contract',
    #         'url': '/web/content/purchase.order/%s/fer_txt/%s?download=true' %(self.id,nombre),
    #     }

class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def create(self, vals):
        res = super(IrAttachment, self).create(vals)

        for attachment in res:
            if attachment.res_model == 'fer.supplier.invoice':
                supplier_invoices = self.env['fer.supplier.invoice'].search([('id','=',attachment.res_id)])
                logging.info("############################### attachment: %s",supplier_invoices.fer_purchase_order_id)
                attachment.res_model = 'purchase.order'
                attachment.res_field = None
                logging.info("############################### attachment: %s",attachment.res_id)
                attachment.res_id = supplier_invoices.fer_purchase_order_id
                logging.info("############################### attachment: %s",attachment.res_id)

                if attachment.name == 'fer_cfdi_xml':
                    attachment.name = supplier_invoices.fer_cfdi_xml_name
                    attachment.mimetype = 'application/xml'

        return res

class PurchaseOrderLine(models.Model): 
    _inherit = "purchase.order.line"


