# -*- coding: utf-8 -*-
{
    'name': "Validación de XML",

    'summary': """
        Permite adjuntar XMLs y validar la cantidad
        """,

    'description': """
        Este desarrollo permite adjuntar facturas XML desde línea 
        a las recepciones de compra, y valida si la cantidad de la factura XML
        corresponde a la cantidad en recepción.
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
                'sale', 
                'stock',
                'account',
                ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/fer_purchase_invoice_view.xml',
        'wizards/fer_supplier_invoice.xml',
        'wizards/message_wizard.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
