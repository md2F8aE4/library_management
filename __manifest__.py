{
    'name': 'Library Management',
    'version': '1.0',
    'author': 'Abdelrahman',
    'depends': ['base', 'stock', 'product', 'account', 'mail', 'portal', 'sale'],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        'data/sequence.xml',
        'views/borrow_book_wizard_views.xml',
        "views/book_view.xml",
        "views/library_member_view.xml",
        'views/borrow_book_views.xml',
        "views/menu.xml",
        'views/portal_templates.xml',
        
    ],

    'application':True,
}
