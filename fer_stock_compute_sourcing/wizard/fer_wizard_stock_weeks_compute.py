import logging
from datetime import datetime, date


from odoo import api, fields, models
_logger = logging.getLogger(__name__)

class FerWizardStockComputeSourcing(models.TransientModel):
    _name = 'fer.wizard.stock.weeks.compute'
    _description = 'Calculo de abastecimiento por semanas'

    fer_date_now = fields.Date(string='Fecha de calculo', readonly=True, default=lambda date: fields.Date.today())
    fer_product_init = fields.Integer(string='Producto inicial')
    fer_product_end = fields.Integer(string='Producto final')
    location_id = fields.Many2one('stock.location', string='Ubicación')
    fer_brand = fields.Many2one('fer.product.brand', string='Marca')
    fer_period_hist = fields.Integer(string='Periodo Historico', help='Mínimo 8 máximo 52 (semanas)', default=8)
    fer_sale_min =  fields.Integer(string='Venta mínima por discriminar', help='Mínimo 0 maximo (periodo histórico / 2)', default=0)
    fer_sale_max =  fields.Integer(string='Venta máxima por discriminar', help='Mínimo 0 maximo (periodo histórico / 2)', default=0)
    fer_days_lab =  fields.Integer(string='Días laborales por semana', help='Mínimo 1 maximo 7', default=6)

    def week_sourcing_calculation(self):
        products_setter = self.fer_setter_init_values()
        weeks_list = self.fer_get_week(products_setter['weeks'])
        for dictionary in weeks_list:
            qty_produts, average = self.fer_sale_week(products_setter['brand'], products_setter['location'], dictionary['week_ini'], dictionary['week_end'])
            dictionary['qty'] = qty_produts
            dictionary['average'] = average

        weeks = self.fer_remove_weeks(weeks_list)
        # self.fer_sale_data(weeks, products_setter)
        # # products, averages, cumulative, words = self.fer_sale_data(products_setter)
        # # stock_history = self.fer_get_history_stock(products, averages, cumulative, words, products_setter['location'])
        # # stock_calculated = self.fer_get_min_max(stock_history)
        # # last_id = self.fer_maker_history_records(stock_calculated)
        # last_id = 2

        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'fer.history.stock.orderpoint',
        #     'view_mode': 'form',
        #     'view_type': 'form',
        #     'res_id': last_id,
        #     'views': [(False, 'form')],
        #     'target': 'current',
        #     }

    def fer_maker_history_records(self, stock_to_created):
        datetime = fields.Datetime.now()
        self.env['fer.history.stock.orderpoint'].sudo().create({'fer_timestamp': datetime})

        hist_efim = self.env['fer.history.stock.orderpoint'].search([('fer_timestamp', '=', datetime)])
        for data in stock_to_created:
            print(data)
            hist_efim.write({'fer_stock_rules_efim_ids': [(0, 0, data)]})

        return hist_efim.id

    def fer_get_min_max(self, stock_to_created):
        for stock in stock_to_created:
            # print(stock['default_code'])
            product = self.env['fer.letters'].search([
                ('fer_letter', '=', stock['fer_product_letter'])
                ])
            # stk_min = round(product.fer_days_min_stock * stock['fer_product_average'])
            stk_max = round(product.fer_days_max_stock * stock['fer_product_average'])
            if stk_max < stock['fer_old_product_min']:
                stock['fer_c_product_min'] = stock['fer_old_product_min']
                stock['fer_c_product_max'] = stock['fer_old_product_max']
            else:
                stock['fer_c_product_min'] = stock['fer_old_product_min']
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
            products_update = [item for item in range(record.fer_product_init, record.fer_product_end+1) if item != 0]
            if len(products_update) == 0:
                products_setter['products_update'] = None
            else:
                products_setter['products_update'] = products_update

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
        dic_stock = dict()
        dic_averages = dict()
        dic_cumulative = dict()
        dic_words = dict()

        if products_range['products_update']:
            prodt = True
        else:
            prodt = False
        for week in weeks:
            domain = [
                ('date', '>=', week['week_ini']),
                ('date', '<=', week['week_end'])]
            stock_move = self.env['stock.move.line'].search(domain)
            timelapse = week['week_end'] - week['week_ini']
            print(timelapse.days())
            # Obtener productos
            if prodt:
                for stock in stock_move:
                    if int(stock.product_id.default_code) in products_range['products_update']:
                        if products_range['brand']:
                            if stock.picking_location_dest_id.name == 'Customers' and stock.product_id.fer_brand_ids.fer_brand_name == products_range['brand']:
                                self.fer_make_dictionary_templates(dic_products, stock.product_id.id, stock.qty_done)
                                if 'Piso' not in stock.location_id.display_name:
                                    dic_stock[stock.product_id.id] = stock.location_id.display_name
                        else:
                            if stock.picking_location_dest_id.name == 'Customers':
                                self.fer_make_dictionary_templates(dic_products, stock.product_id.id, stock.qty_done)
                                if 'Piso' not in stock.location_id.display_name:
                                    dic_stock[stock.product_id.id] = stock.location_id.display_name
                    else:
                        continue
            else:
                for stock in stock_move:
                    if products_range['brand']:
                        if stock.picking_location_dest_id.name == 'Customers' and stock.product_id.fer_brand_ids.fer_brand_name == products_range['brand']:
                            self.fer_make_dictionary_templates(dic_products, stock.product_id.id, stock.qty_done)
                            if 'Piso' not in stock.location_id.display_name:
                                    dic_stock[stock.product_id.id] = stock.location_id.display_name
                    else:
                        if stock.picking_location_dest_id.name == 'Customers':
                            self.fer_make_dictionary_templates(dic_products, stock.product_id.id, stock.qty_done)
                            if 'Piso' not in stock.location_id.display_name:
                                    dic_stock[stock.product_id.id] = stock.location_id.display_name

            # Obtener promedios
            for key in dic_products.keys():
                    average = dic_products[key] / record.fer_timelapse
                    self.fer_make_dictionary_templates(dic_averages, key, average)

            # Obtener acumulados
            for key in dic_averages.keys():
                cumulative = (dic_averages[key] / sum(dic_averages.values())) * 100
                self.fer_make_dictionary_templates(dic_cumulative, key, cumulative)

            # Asignación de Letras
            word = self.env['fer.letters'].search([])
            letters = {item.fer_letter:item.fer_percent for item in word}
            for key in dic_cumulative.keys():
                val =  100 - dic_cumulative[key]
                if letters['A'] >= val:
                    self.fer_make_dictionary_templates(dic_words, key, 'A')
                    continue
                if letters['A'] < val or val <= letters['B']:
                    self.fer_make_dictionary_templates(dic_words, key, 'B')
                    continue
                else:
                    self.fer_make_dictionary_templates(dic_words, key, 'C')
        print(dic_products, dic_averages, dic_cumulative, dic_words)
        return dic_products, dic_averages, dic_cumulative, dic_words

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

    def fer_get_history_stock(self, products, averages, cumulative, words, location):
        old_stock_rules = self.env['stock.warehouse.orderpoint'].search([])
        stock_dicts = list()
        common_keys = list()

        prod_keys = [key for key in products.keys()]
        rule_keys = [rule.product_id.id for rule in old_stock_rules]
        for key in prod_keys:
            if key in rule_keys:
                common_keys.append(key)
                # prod_keys.remove(key)

        for rule in old_stock_rules:
            if rule.product_id.id in prod_keys and rule.location_id.complete_name == location:
                stock_dicts.append({
                    'fer_qty_done' : products[rule.product_id.id],
                    'fer_product_average': averages[rule.product_id.id],
                    'fer_product_cumulative': cumulative[rule.product_id.id],
                    'fer_product_letter': words[rule.product_id.id],
                    'product_id': rule.product_id.id,
                    'location_id': rule.location_id.id,
                    'fer_old_product_min': rule.product_min_qty,
                    'fer_old_product_max': rule.product_max_qty,
                    })
                continue

        # for key in prod_keys:
        #     stock_dicts.append({'product_id': key,
        #         'fer_qty_done' : products[key],
        #         'fer_product_average': averages[key],
        #         'fer_product_cumulative': cumulative[key],
        #         'fer_product_letter': words[key],
        #         'location_id': self.location_id.id,
        #         'fer_old_product_min': 0,
        #         'fer_old_product_max': 0,
        #         })

        return stock_dicts
