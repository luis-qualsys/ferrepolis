from odoo import models, fields, api
from odoo.exceptions import Warning
from odoo.exceptions import AccessError, UserError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def create_mrp_from_pos(self, products):
        product_ids = []
        if products:
            for product in products:
                flag = 1
                if product_ids:
                    for product_id in product_ids:
                        if product_id['id'] == product['id']:
                            product_id['qty'] += product['qty']
                            flag = 0
                if flag:
                    product_ids.append(product)
            for prod in product_ids:
                if prod['qty'] > 0:
                    product = self.env['product.product'].search([('id', '=', prod['id'])])
                    bom_count = self.env['mrp.bom'].search([('product_tmpl_id', '=', prod['product_tmpl_id'])])
                    if bom_count:
                        bom_temp = self.env['mrp.bom'].search([('product_tmpl_id', '=', prod['product_tmpl_id']),
                                                                ('product_id', '=', False)])
                        bom_prod = self.env['mrp.bom'].search([('product_id', '=', prod['id'])])
                        if bom_prod:
                            bom = bom_prod[0]
                        elif bom_temp:
                            bom = bom_temp[0]
                        else:
                            bom = []
                        if bom:
                            vals = {
                                'activity_ids': [],
                                'origin': 'POS-' + prod['pos_reference'],
                                'product_id': prod['id'],
                                'product_tmpl_id': prod['product_tmpl_id'],
                                'product_uom_id': prod['uom_id'],
                                'product_qty': prod['qty'],
                                'bom_id': bom.id,
                                'picking_type_id': bom.picking_type_id.id,
                                'is_locked': False,
                                'message_follower_ids': [],
                                'lot_producing_id': False,
                                'message_ids': [],
                                'move_byproduct_ids': [],
                                'location_src_id': bom.picking_type_id.default_location_src_id.id,
                                'location_dest_id': bom.picking_type_id.default_location_dest_id.id,
                            }
                            mrp_order = self.env['mrp.production'].new(vals)
                            mrp_order.onchange_product_id()
                            mrp_order._onchange_product_qty()
                            mrp_order._onchange_bom_id()
                            mrp_order._onchange_date_planned_start()
                            mrp_order.product_qty = prod['qty']
                            mrp_order._onchange_move_raw()
                            mrp_order._onchange_move_finished()
                            data = mrp_order._convert_to_write(mrp_order._cache)

                            data['move_raw_ids'] = self.make_lines_ids(data['move_raw_ids'])
                            data['move_finished_ids'] = self.make_lines_ids(data['move_finished_ids'])
                            # data['product_qty'] = prod['qty']
                            # print('Before to create', data)
                            # del data['move_finished_ids']
                            mrp = self.create(data)
                            # print('######### Cantidad', mrp.product_qty)
                            # mrp.onchange_product_id()
                            # mrp._onchange_product_qty()
                            # mrp._onchange_bom_id()
                            # mrp._onchange_date_planned_start()
                            # mrp._onchange_move_raw()
                            # mrp._onchange_move_finished()
                            mrp._onchange_location()
                            mrp._onchange_location_dest()
                            mrp.onchange_picking_type()
                            mrp._onchange_producing()
                            mrp._onchange_lot_producing()
                            mrp._onchange_workorder_ids()
                            # print('After to create', data)
                            # print('Finished', data.move_finished_ids)
                            # print(mrp)
                            return mrp

        return True

    def make_lines_ids(self, raw_moves_ids):
        final = []
        if len(raw_moves_ids) >= 1:
            for item in raw_moves_ids:
                if type(item[2]) == dict:
                    final_moves_line_ids = [0, 0]
                    final_moves_line_ids.append(item[2])
                    final.append(final_moves_line_ids)

        return final


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    to_make_mrp = fields.Boolean(string='Crear MRP Order',
                                help="Verifica si el producto deberia hacer una order de manufactura")

    @api.onchange('to_make_mrp')
    def onchange_to_make_mrp(self):
        if self.to_make_mrp:
            if not self.bom_count:
                raise Warning('Favor de configurar la lista de materiales del producto.')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('to_make_mrp')
    def onchange_to_make_mrp(self):
        if self.to_make_mrp:
            if not self.bom_count:
                raise Warning('Favor de configurar la lista de materiales del producto.')