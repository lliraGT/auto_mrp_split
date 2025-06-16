# -*- coding: utf-8 -*-

{
    'name': 'Auto MRP Split with Fixed Batches',
    'version': '1.0',
    'category': 'Manufacturing',
    'summary': 'Automatically split MOs with fixed batch quantities',
    'description': """
        This module automatically splits manufacturing orders for specific products
        into fixed batch quantities:
        
        For the product "Tortas Pollo LifeStyle - Suscripción":
        - Minimum 5 batches
        - Each batch exactly 41 units
        - Automatic split button added to manufacturing orders
    """,
    'author': 'Custom',
    'depends': ['mrp'],
    'data': [
        'views/mrp_production_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}