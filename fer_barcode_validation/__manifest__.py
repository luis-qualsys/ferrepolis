# -*- coding: utf-8 -*-
{
    'name': "Validación de recepción con códigos de barras",

    'summary': """
        Validar la cantidad en la recepción.
        """,

    'description': """
        Este desarrollo valida las cantidades de compra 
        si la cantidad no sobrepasa cantidad en recepción.
    """,

    'author': "Qualsys Consulting",
    'website': "https://www.qualsys.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 
                'purchase', 
                'stock',
                'barcodes',
                ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'static/src/xml/bar_validation.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
