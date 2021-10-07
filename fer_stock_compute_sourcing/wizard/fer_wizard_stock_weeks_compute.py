import logging
from datetime import date
from operator import itemgetter


from odoo import api, fields, models
_logger = logging.getLogger(__name__)

class FerWizardStockComputeSourcing(models.TransientModel):
    _name = 'fer.wizard.stock.weeks.compute'
    _description = 'Calculo de abastecimiento por semanas'

    fer_date_now = fields.Date(string='Fecha de calculo', readonly=True, default=lambda date: fields.Date.today())
    fer_product_id_initial = fields.Many2one('product.product', string='Producto inicial')
    fer_product_id_ended = fields.Many2one('product.product', string='Producto final')
    location_id = fields.Many2one('stock.location', string='Ubicación', required=True, domain=[('fer_search_flag', '=', True)])
    fer_brand = fields.Many2one('fer.product.brand', string='Marca')
    fer_period_hist = fields.Integer(string='Periodo Historico', help='Mínimo 8 máximo 52 (semanas)', default=8)
    fer_sale_min =  fields.Integer(string='Venta mínima por discriminar', help='Mínimo 0 maximo (periodo histórico / 2)', default=0)
    fer_sale_max =  fields.Integer(string='Venta máxima por discriminar', help='Mínimo 0 maximo (periodo histórico / 2)', default=0)
    fer_days_lab =  fields.Integer(string='Días laborales por semana', help='Mínimo 1 maximo 7', default=6)

    @api.model
    def default_get(self, fields):
        mode = super(FerWizardStockComputeSourcing, self).default_get(fields)
        lines_suggest = [(6,0,0)]
        locations = self.env['fer.stock.computer.parms'].search([('id', '=', 1)])
        ids = 0
        for loc in locations[0].location_ids:
            ids = loc.id
            lines_suggest.append((0, 0, {
                'id': loc.id,
                'complete_name': loc.complete_name
            }))
        mode.update({
            'location_id': ids,
        })
        return mode

    def week_sourcing_calculation(self):
        products_setter = self.fer_setter_init_values()
        weeks_list = self.fer_get_week(products_setter['weeks'])
        for dictionary in weeks_list:
            qty_produts, average = self.fer_sale_week(products_setter['brand'], products_setter['location'], dictionary['week_ini'], dictionary['week_end'])
            dictionary['qty'] = qty_produts
            dictionary['average'] = average

        weeks = self.fer_remove_weeks(weeks_list)
        products, averages, cumulative, participation, words = self.fer_sale_data(weeks, products_setter)
        stock_history = self.fer_get_history_stock(products, averages, cumulative, participation, words)
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
            'location_id': self.location_id.complete_name,
            'fer_brand': self.fer_brand.fer_brand_name,
            'fer_origin': 'stock_week',
            'fer_prod_init': self.fer_product_id_initial.default_code,
            'fer_prod_end': self.fer_product_id_ended.default_code,
            })

        hist_efim = self.env['fer.history.stock.orderpoint'].search([('fer_timestamp', '=', datetime)])
        for data in stock_to_created:
            hist_efim.write({'fer_stock_rules_efim_ids': [(0, 0, data)]})

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

    def fer_remove_weeks(self, weeks):
        new_weeks=list()
        lweeks = []
        laverage = []
        for week in weeks:
            lweeks.append(week['week'])
            laverage.append(week['average'])
        if self.fer_sale_min != 0:
            for counter in range(self.fer_sale_min):
                lweeks.pop(laverage.index(min(laverage)))
                laverage.pop(laverage.index(min(laverage)))

        if self.fer_sale_max != 0:
            for counter in range(self.fer_sale_max):
                lweeks.pop(laverage.index(max(laverage)))
                laverage.pop(laverage.index(max(laverage)))

        for week in weeks:
            if week['week'] in lweeks:
                new_weeks.append(week)

        return new_weeks

    def fer_sale_week(self, brand, location, date_ini, date_end):
        domain = [
            ('date', '>=', date_ini),
            ('date', '<=', date_end)]
        stock_move = self.env['stock.move.line'].search(domain)
        # Obtener productos
        qty_produts = 0

        if brand and location:
            for stock in stock_move:
                if location in stock.location_id.display_name and brand == stock.product_id.fer_brand_ids.fer_brand_name and stock.picking_location_dest_id.name == 'Customers':
                    qty_produts += stock.qty_done
        elif location:
            for stock in stock_move:
                if location in stock.location_id.display_name and stock.picking_location_dest_id.name == 'Customers':
                    qty_produts += stock.qty_done
        elif brand:
            for stock in stock_move:
                if brand == stock.product_id.fer_brand_ids.fer_brand_name and stock.picking_location_dest_id.name == 'Customers':
                    qty_produts += stock.qty_done

        average = qty_produts / self.fer_days_lab
        return qty_produts, average

    def fer_get_week(self, weeks):
        weeks_data = []
        anio, week_end = self.fer_date_now.isocalendar()[0], self.fer_date_now.isocalendar()[1]
        end = self.fer_days_lab
        for week in range(week_end-weeks, week_end+1):
            dict_weeks = dict()
            dict_weeks['week'] = week
            dict_weeks['week_ini'] = date.fromisocalendar(anio, week, 1)
            dict_weeks['week_end'] = date.fromisocalendar(anio, week, end)
            weeks_data.append(dict_weeks)

        return weeks_data

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
            if record.fer_period_hist:
                products_setter['weeks'] = record.fer_period_hist
            else:
                products_setter['weeks'] = record.fer_period_hist

        return products_setter

    def fer_sale_data(self, weeks, products_range):
        dic_products = dict()
        dic_averages = dict()
        dic_cumulative = dict()
        dic_participation = dict()
        dic_words = dict()
        timelapse = 0

        for week in weeks:
            domain = [
                ('date', '>=', week['week_ini']),
                ('date', '<=', week['week_end'])]
            stock_move = self.env['stock.move.line'].search(domain)
            timelapse += self.fer_days_lab

            # Obtener productos
            for stock in stock_move:
                if stock.product_id.default_code in products_range['products_update']:
                    if products_range['brand']:
                        if stock.picking_location_dest_id.name == 'Customers' and stock.product_id.fer_brand_ids.fer_brand_name == products_range['brand']:
                            self.fer_make_dictionary_templates(dic_products, stock.product_id.id, stock.qty_done)
                    else:
                        if stock.picking_location_dest_id.name == 'Customers':
                            self.fer_make_dictionary_templates(dic_products, stock.product_id.id, stock.qty_done)

        # Obtener promedios
        for key in dic_products.keys():
            average = dic_products[key] / timelapse
            self.fer_make_dictionary_templates(dic_averages, key, average)

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
        
        _logger.info("Calculos finalizados")
        return dic_products, dic_averages, dic_cumulative, dic_participation, dic_words

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

    def fer_get_history_stock(self, products, averages, cumulative, participation, words):
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
