# -*- coding = utf - 8 -*-
import base64
import logging
_logger = logging.getLogger(__name__)
from lxml import etree

from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError


class SupplierInvoice(models.TransientModel): 
    _name = "fer.supplier.invoice"
    _description = "Factura de recepción"
    _order = "id desc"

    name = fields.Char(string="Documento asociado")
    fer_cfdi_xml = fields.Binary(string="XML")
    fer_cfdi_xml_name = fields.Char(string="XML ", default="", copy=False)
    # fer_cfdi_pdf = fields.Binary(string="PDF")
    # fer_cfdi_pdf_name = fields.Char(string="PDF ", default="", copy=False)
    fer_purchase_order_id = fields.Many2one('purchase.order', string="Factura")
    # fer_partner_country = fields.Char(string="País", related='fer_stock_picking_id.partner_id.country_id.name')
    fer_l10n_mx_edi_cfdi_uuid = fields.Char(string="UUID", help="Folio fiscal para factura de proveedores")
    fer_state = fields.Selection([
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ],string="Estado")
    # _sql_constraints = {
    # 	('unique_cfdi_name', 'unique(name)', 'El documento de Validación seleccionado ya ha sido ocupado en otro registro.\n\nSeleccione otro documento de Validación.'),
    # 	('unique_fer_cfdi_uuid', 'unique(fer_l10n_mx_edi_cfdi_uuid)', 'El documento XML seleccionado ya ha sido ocupado en otro registro.')
    # }

    @api.onchange('fer_cfdi_xml','fer_purchase_order_id')
    def xml_validation(self):
        if self.fer_cfdi_xml:
            try:
                xml_data=base64.decodestring(self.fer_cfdi_xml)
                xml_tree_root = etree.fromstring(xml_data)
                NSMAP = {
                    'xsi':'http://www.w3.org/2001/XMLSchema-instance',
                    'cfdi':'http://www.sat.gob.mx/cfd/3',
                    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
                    }
                complement = xml_tree_root.find("cfdi:Complemento", NSMAP)
                stamp = complement.find("tfd:TimbreFiscalDigital", NSMAP)
                uuid = stamp.attrib['UUID']

                attachments = self.env['fer.supplier.invoice'].search([('fer_l10n_mx_edi_cfdi_uuid','=',uuid)])

            except etree.ParseError:
                raise ValidationError("El formato de la factura no es correcto. Por favor verifique la información.")

    def unlink(self):
        for attachments in self:
            attachs = self.env['ir.attachment'].sudo().search([
                '&',('res_id','=',attachments.fer_purchase_order_id.id),
                ('name','=',attachments.fer_cfdi_xml_name),
                ])

            for attachment in attachs:
                attachment.unlink()

        res = super(SupplierInvoice, self).unlink()
        return res

    @api.model
    def create(self, vals):
        ## Crear las líneas de diferencia en nueva pestaña
        purchase_id = self.env['purchase.order'].browse(self._context.get('active_id'))
        if purchase_id.partner_id.category_id.name == "Mayorista":
            supplier_lines = self.env['fer.supplier.invoice'].search([('fer_purchase_order_id','=',purchase_id.id)])

            for line in supplier_lines:
                line.unlink()
            vals['fer_purchase_order_id']=purchase_id.id
        res = super(SupplierInvoice, self).create(vals)

        if purchase_id.partner_id.category_id.name == "Mayorista":
            if res.fer_cfdi_xml:
                try:
                    flag = 0
                    xml_data=base64.decodestring(res.fer_cfdi_xml)
                    xml_tree_root = etree.fromstring(xml_data)
                    NSMAP = {
                        'xsi':'http://www.w3.org/2001/XMLSchema-instance',
                        'cfdi':'http://www.sat.gob.mx/cfd/3',
                        'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
                        }
                    complement = xml_tree_root.find("cfdi:Complemento", NSMAP)
                    stamp = complement.find("tfd:TimbreFiscalDigital", NSMAP)
                    uuid = stamp.attrib['UUID']

                    complement2 = xml_tree_root.find("cfdi:Conceptos", NSMAP)
                    stamp2 = complement2.findall("cfdi:Concepto", NSMAP)

                    folio = xml_tree_root.attrib['Folio']
                    logging.info("############################### folio: %s",folio)
                    purchase_id.partner_ref = folio
                    purchase_lines = purchase_id.order_line

                    for element in stamp2:
                        counterXML=0
                        cantidad=float(element.attrib['Cantidad'])
                        producto=element.attrib['NoIdentificacion']
                        precio=float(element.attrib['ValorUnitario'])
                        impuesto = element.find("cfdi:Impuestos", NSMAP)
                        traslados = impuesto.find("cfdi:Traslados", NSMAP)
                        traslado = traslados.find("cfdi:Traslado", NSMAP)
                        iva=float(traslado.attrib['TasaOCuota']) * 100
                        
                        product = self.env['product.product'].search([('barcode','=',producto)])
                        if len(product) == 0:
                            raise ValidationError("Hay productos en la factura XML que no se encuentran registrados en la base de datos.\nVerifique su información.")
                        logging.info("############################### producto: %s",producto)
                        logging.info("############################### product: %s",len(product))
                        logging.info("############################### cantidad: %s",cantidad)
                        for line in purchase_lines:
                            logging.info("############################### linea: %s",line)
                            if line.product_id.barcode == producto:
                                counterXML=1
                                logging.info("############################### coincidencia en producto")
                                # if line.product_qty == cantidad:
                                logging.info("############################### precios: %s %s",line.price_unit,precio)
                                if len(line.taxes_id) > 1:
                                    raise ValidationError("Hay productos con más de un impuesto en la solicitud. Verifique su información.")
                                logging.info("############################### ivas: %s %s",line.taxes_id.amount,iva)
                                if line.product_qty == cantidad and line.price_unit==precio and line.taxes_id.amount==iva:
                                    logging.info("############################### coincidencia en cantidades, precio e iva")
                                else:
                                    flag = 1
                                    logging.info("############################### se cambia la cantidad y se genera reg de dif")
                                    new_tax = self.env['account.tax'].search([('amount','=',iva),('type_tax_use','=','purchase')])
                                    logging.info("############################### new tax: %s",new_tax)
                                    vals={
                                        'fer_product_id': product.id,
                                        'fer_po_id': purchase_id.id,
                                        'fer_qty_original': line.product_qty,
                                        'fer_qty_received': cantidad,
                                        'fer_qty_diff': cantidad - line.product_qty,
                                        'fer_price_original': line.price_unit,
                                        'fer_price_new': precio,
                                        'fer_tax_original': line.taxes_id.amount,
                                        'fer_tax_new': new_tax,
                                    }
                                    purchase_id.fer_log_invoice_lines.create(vals)

                        if counterXML==0:
                            flag = 1
                            new_tax = self.env['account.tax'].search([('amount','=',iva),('type_tax_use','=','purchase')])

                            logging.info("############################### Crear registro de diferencia")
                            vals={
                                'fer_product_id': product.id,
                                'fer_po_id': purchase_id.id,
                                'fer_qty_original': 0,
                                'fer_qty_received': cantidad,
                                'fer_qty_diff': cantidad,
                                'fer_price_new': precio,
                                'fer_tax_new': new_tax,
                            }
                            purchase_id.fer_log_invoice_lines.create(vals)

                    for line in purchase_lines:
                        counterPO=0
                        for element in stamp2:
                            producto = element.attrib['NoIdentificacion']
                            precio = float(element.attrib['ValorUnitario'])
                            impuesto = element.find("cfdi:Impuestos", NSMAP)
                            traslados = impuesto.find("cfdi:Traslados", NSMAP)
                            traslado = traslados.find("cfdi:Traslado", NSMAP)
                            iva = float(traslado.attrib['TasaOCuota']) * 100
                            new_tax = self.env['account.tax'].search([('amount','=',iva),('type_tax_use','=','purchase')])

                            if product == False:
                                raise ValidationError("Algunos productos en el XML no se encuentran registrados en la base de datos. Verifique su información.")
                            if line.product_id.barcode == producto:
                                counterPO=1
                        if counterPO==0:
                            flag = 1
                            logging.info("############################### Crear linea de diferencia")

                            vals={
                                'fer_product_id': line.product_id.id,
                                'fer_po_id': purchase_id.id,
                                'fer_qty_original': line.product_qty,
                                'fer_qty_received': 0,
                                'fer_qty_diff': -line.product_qty,
                                'fer_price_original': line.price_unit,
                                'fer_price_new': line.price_unit,
                                'fer_tax_original': line.taxes_id.amount,
                                'fer_tax_new': line.taxes_id,
                            }
                            purchase_id.fer_log_invoice_lines.create(vals)

                    res.fer_l10n_mx_edi_cfdi_uuid = uuid
                    res.fer_purchase_order_id.fer_invoice = res.fer_cfdi_xml_name
                    if flag == 0:
                        res.fer_state = 'active'
                    else:
                        res.fer_state = 'inactive'

                except etree.ParseError:
                    raise ValidationError("El formato de la factura no es correcto. Por favor verifique la información.")
                except KeyError:
                    raise ValidationError("La factura no contiene la información necesaria para realizar el proceso. Por favor verifique la información.")
        return res

    def action_create(self):
        print("Boton")
        logging.info("############################### action_create = %s",self)

        if self.fer_state == 'active':
            message_id = self.env['message.wizard'].create({'message': "Pedido completo."})
        else:
            message_id = self.env['message.wizard'].create({'message': "Hay algunas diferencias entre la factura y la solicitud. Consulte la pestaña Diferencias de Solicitud."})

        return {
            'name': 'Mensaje',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'message.wizard',
            # pass the id
            'res_id': message_id.id,
            'target': 'new'
        }
