{
    'name': 'ABS SYNC DATA',
    'version': '16.0.170524',
    'category': 'AUM Business System/ Sync Data',
    'summary': 'SYNC DATA',
    'author': 'AUM Company',
    'website': 'https://aum.edu.vn/',
    'depends': ['base', 'combo_product', 'sale', 'sale_management', 'loyalty'],
    'data': [
        'security/ir.model.access.csv',
        'views/loyalty_program_view.xml',
        'views/loyalty_reward_views.xml',
        'views/product_template_view.xml',
        'views/th_product_pricelist_views.xml',
        'views/promotional_event.xml',
        'views/th_sync_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
