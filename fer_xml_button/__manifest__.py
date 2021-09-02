# -*- coding: utf-8 -*-
{
    'name': "Botón de XML",

    'summary': """
        Complemento que agrega el botón XML
        """,

    'description': """
        Complemento a recepción de XMLs.
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
        'views/fer_xml_button.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
