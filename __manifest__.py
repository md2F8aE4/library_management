{
    'name': 'Library Management',
    'version': '1.0',
    'author': 'Abdelrahman',
    'depends': ['base', 'stock', 'product', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/book_view.xml',
    ],

    'application':True,
}
