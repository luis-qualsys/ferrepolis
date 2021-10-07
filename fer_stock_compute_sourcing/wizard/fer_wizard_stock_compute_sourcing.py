import logging
from operator import itemgetter

from odoo import api, fields, models
_logger = logging.getLogger(__name__)

class FerWizardStockComputeSourcing(models.TransientModel):
    _name = 'fer.wizard.stock.compute.sourcing'
    _inherit = ['fer.compute.model.search']
    _description = 'Calculo de abastecimiento'

    fer_product_id_initial = fields.Many2one('product.product', string='Producto inicial')
    fer_product_id_ended = fields.Many2one('product.product', string='Producto final')

    def sourcing_calculation(self):
        # Crear historial de calculos pasados
        products_setter = self.fer_setter_init_values()
        products, averages, cumulative, words, participation = self.fer_sale_data(products_setter)
        stock_history = self.fer_get_history_stock(products, averages, cumulative, words, participation)
        stock_calculated = self.fer_get_min_max(stock_history)
        last_id = self.fer_maker_history_records(stock_calculated)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fer.history.stock.orderpoint',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': last_id,
            'views': [(False, 'form')],
            'target': 'current',
            }

    def fer_maker_history_records(self, stock_to_created):
        datetime = fields.Datetime.now()
        self.env['fer.history.stock.orderpoint'].sudo().create({
            'fer_timestamp': datetime,
            'fer_date_init': self.fer_date_init,
            'fer_date_end': self.fer_date_end,
            'location_id': self.location_id.complete_name,
            'fer_brand': self.fer_brand.fer_brand_name,
            'fer_origin': 'stock',
            'fer_prod_init': self.fer_product_id_initial.default_code,
            'fer_prod_end': self.fer_product_id_ended.default_code,
            })

        hist_efim = self.env['fer.history.stock.orderpoint'].search([('fer_timestamp', '=', datetime)])
        for data in stock_to_created:
            hist_efim.write({'fer_stock_rules_efim_ids': [(0, 0, data)]})
        
        _logger.info("Registro de reglas de stock creado %s" % hist_efim.id)
        return hist_efim.id

    def fer_get_min_max(self, stock_to_created):
        for stock in stock_to_created:
            words = self.env['fer.stock.computer.parms'].search([('location_ids', '=', self.location_id.id)], limit=1).mapped('fer_letters_id')
            for item in words:
                if item.fer_letter == stock['fer_product_letter']:
                    stk_min = round(item.fer_days_min_stock * stock['fer_product_average'])
                    stk_max = round(item.fer_days_max_stock * stock['fer_product_average'])
                    stock['fer_c_product_min'] = stk_min
                    stock['fer_c_product_max'] = stk_max
        return stock_to_created

    def fer_setter_init_values(self):
        products_setter = dict()
        # Setter inputs
        for record in self:
            prods = self.env['product.template'].search([('type', 'ilike', 'product')]).mapped('default_code')
            if record.fer_product_id_initial and record.fer_product_id_ended:
                prods.sort()
                initial = 0
                final = -1
                if record.fer_product_id_initial.default_code in prods:
                    initial = prods.index(record.fer_product_id_initial.default_code)
                if record.fer_product_id_ended.default_code in prods:
                    final = prods.index(record.fer_product_id_ended.default_code) + 1
                products_setter['products_update'] = prods[initial:final]
            else:
                products_setter['products_update'] = prods

            if record.fer_brand.fer_brand_name:
                products_setter['brand'] = record.fer_brand.fer_brand_name
            else:
                products_setter['brand'] = None

            if record.location_id:
                products_setter['location'] = record.location_id.complete_name
            else:
                products_setter['location'] = None
            
            if record.account_ids:
                products_setter['accounts'] = record.account_ids
            else:
                products_setter['accounts'] = None
            if record.partner_id:
                products_setter['partners'] = record.partner_id
            else:
                products_setter['partners'] = None

        return products_setter

    def fer_sale_data(self, products_range):
        dic_products = dict()
        dic_averages = dict()
        dic_cumulative = dict()
        dic_participation = dict()
        dic_words = dict()
        picking_locations = ['Customers', 'Production']

        if products_range['partners'] or products_range['accounts']:
            invoices_desc = self.fer_get_invoices_partner(products_range['accounts'], products_range['partners'])
        else: 
            invoices_desc = {}

        for record in self:
            domain = [
                ('date', '>=', record.fer_date_init),
                ('date', '<=', record.fer_date_end)]
            stock_move = self.env['stock.move.line'].search(domain)

            # Obtener productos
            for stock in stock_move:
                if stock.product_id.default_code in products_range['products_update']:
                    if products_range['brand']:
                        if stock.picking_location_dest_id.name in picking_locations and stock.product_id.fer_brand_ids.fer_brand_name == products_range['brand']:
                            self.fer_make_dictionary_templates(dic_products, stock.product_id.id, stock.qty_done)
                    else:
                        if stock.picking_location_dest_id.name in picking_locations:
                            self.fer_make_dictionary_templates(dic_products, stock.product_id.id, stock.qty_done)

            # Obtener promedios
            for key in dic_products.keys():
                if key in invoices_desc:
                    average = (dic_products[key] - invoices_desc[key]) /  (record.fer_timelapse - record.fer_omit_days)
                    self.fer_make_dictionary_templates(dic_averages, key, average)
                else:
                    average = dic_products[key] /  (record.fer_timelapse - record.fer_omit_days)
                    self.fer_make_dictionary_templates(dic_averages, key, average)

            # Obtener participation
            for key in dic_averages.keys():
                cumulative = (dic_averages[key] / sum(dic_averages.values())) * 100
                self.fer_make_dictionary_templates(dic_cumulative, key, cumulative)

            # Obtener acumulados
            participative = sorted(dic_cumulative.items(), key=itemgetter(1), reverse=True)
            cumulative = 0
            for tupla in participative:
                for key in dic_cumulative.keys():
                    if tupla[0] == key:
                        cumulative += tupla[1]
                        self.fer_make_dictionary_templates(dic_participation, tupla[0], cumulative)

            # Asignación de Letras
            word = self.env['fer.stock.computer.parms'].search([('location_ids', '=', self.location_id.id)], limit=1)
            words = word.mapped('fer_letters_id')
            letters = {item.fer_letter:item.fer_percent for item in words}
            for key in dic_participation.keys():
                val =  dic_participation[key]
                if letters['C'] == round(val):
                    self.fer_make_dictionary_templates(dic_words, key, 'C')
                    continue
                elif letters['C'] > round(val) and round(val) >= letters['B']:
                    self.fer_make_dictionary_templates(dic_words, key, 'B')
                    continue
                else:
                    self.fer_make_dictionary_templates(dic_words, key, 'A')

        return dic_products, dic_averages, dic_cumulative, dic_words, dic_participation

    def fer_maker_dictionary_array(self, dic_products, dic_averages, dic_cumulative, dic_words, new_data):
        new_data = list()
        if len(dic_products) != 0:
            for key in dic_products.keys():
                new_data.append({
                    'product_id': key,
                    'fer_qty_done' : dic_products[key],
                    'fer_product_average': dic_averages[key],
                    'fer_product_cumulative': dic_cumulative[key],
                    'fer_product_letter': dic_words[key]
                })

        return new_data

    def fer_make_dictionary_templates(self, dictionary_empty, key, value):
        if key in dictionary_empty:
            dictionary_empty[key] += value
        else:
            dictionary_empty[key] = value

    def fer_get_invoices_partner(self, invoices_omit, partner_omit):
        invoices_desc = dict()
        state_dont = ['cancel', 'draft']
        invoices = self.env['account.move'].search([
            ('invoice_date', '>=', self.fer_date_init), 
            ('invoice_date', '<=', self.fer_date_end)
            ])

        if invoices_omit:
            invoices_omit = [invoice.id for invoice in invoices_omit]
            for invoice in invoices:
                if invoice.id in invoices_omit and invoice.state not in state_dont:
                    for line in invoice.line_ids:
                        if line.product_id.id and line.quantity >= 0:
                            self.fer_make_dictionary_templates(invoices_desc, line.product_id.id, line.quantity)

        if partner_omit:
            partner_omit = [partner.id for partner in partner_omit]
            for invoice in invoices:
                if invoice.partner_id.id in partner_omit and invoice.state not in state_dont:
                    for line in invoice.line_ids:
                        if line.product_id.id and line.quantity >= 0:
                            self.fer_make_dictionary_templates(invoices_desc, line.product_id.id, line.quantity)
        return invoices_desc

    def fer_get_history_stock(self, products, averages, cumulative, words, participation):
        old_stock_rules = self.env['stock.warehouse.orderpoint'].search([])
        stock_dicts = list()
        prod_keys = [key for key in products.keys()]

        for rule in old_stock_rules:
            if rule.product_id.id in prod_keys:
                if rule.product_id.id in products.keys() and 'Piso' not in rule.location_id.complete_name:
                    stock_dicts.append({
                        'fer_qty_done' : products[rule.product_id.id],
                        'fer_product_average': averages[rule.product_id.id],
                        'fer_product_participation': cumulative[rule.product_id.id],
                        'fer_product_cumulative': participation[rule.product_id.id],
                        'fer_product_letter': words[rule.product_id.id],
                        'product_id': rule.product_id.id,
                        'location_id': rule.location_id.id,
                        'fer_old_product_min': rule.product_min_qty,
                        'fer_old_product_max': rule.product_max_qty,
                        })
                    continue

        return stock_dicts
