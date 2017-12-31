# -*- coding: utf-8 -GPK*-

{
    'name': 'Indrajith',
    'version': '1.0',
    "author": 'Yali Technologies',
    "website": 'http://www.yalitechnologies.com/',
    'category': 'Hospital',
    'sequence': 15,
    'summary': 'Hospital Management',
    'description': 'Hospital Management',
    'depends': ['base', 'mail'],
    'data': [
        'data/stock_location.xml',
        'menu/main_menu.xml',
        'views/product/product_group.xml',
        'views/product/product_sub_group.xml',
        'views/product/product_uom.xml',
        'views/product/product_tax.xml',
        'views/product/product.xml',
        'views/product/product_purchase.xml',
        'views/product/product_sales.xml',
        'menu/product_menu.xml',
        'views/store/product_stock.xml',
        'views/store/stock_location.xml',
        'views/store/store_request.xml',
        'views/store/store_scrap.xml',
        'menu/store_menu.xml',
        'views/purchase/indent.xml',
        'menu/purchase_menu.xml',
    ],
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
