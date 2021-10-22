# -*- coding: utf-8 -*-
{
    'name': "Reabastecimiento de Stock",
    'summary': """Calculo de reabastecimiento de stock Ferrepolis""",
    'author': "Qualsys Consulting",
    'website': "https://www.qualsys.com.mx/",
    'category': 'Inventary',
    'version': '14.0.1',
    'sequence': 10,
    'depends':[
		'base',
        'stock',
        'product',
        'account'
    ],
    'data':[
        'security/ir.model.access.csv',
        'views/fer_history_stock_orderpoint_views.xml',
        'views/fer_product_template_views_inherit.xml',
        'views/fer_table_stock_compute_views.xml',
        'views/fer_product_brand_views.xml',
        'wizard/fer_wizard_stock_compute_sourcing_view.xml',
        'wizard/fer_wizard_stock_weeks_compute_views.xml',
        'views/fer_template_edit_button.xml'
    ],
    'application': True
}
