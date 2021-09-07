# -*- coding = utf - 8 -*-
import logging
_logger = logging.getLogger(__name__)

from odoo import models, fields, api


class StockPicking(models.Model): 
    _inherit = "stock.picking"


    def get_provider_cat(self,barcode=False):
        flag=0
        for category in self.partner_id.category_id:
            if category.name=="Mayorista":
                flag=1
        if flag==1:
            return "Mayorista"
        else:
            return "otro"
