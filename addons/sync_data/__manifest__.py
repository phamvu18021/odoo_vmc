{
    'name': 'SYNC DATA',
    'version': '16.0',
    'category': 'AUM Business System/ Sync Data',
    'summary': 'SYNC DATA',
    'author': 'AUM Company',
    'website': 'https://aum.edu.vn/',
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/sync_config_views.xml'
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
