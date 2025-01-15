{
    'name': 'Vmc User',
    'summary': "Vmc User",
    'description': """
     Vmc User.
               ========================
    """,

    'author': 'AUM it',
    'website': '',
    'category': 'AUM Business System/Vmc User',
    'version': '1.1',
    'depends': ['base', 'contacts', 'vmc_product'],
    'data': [
        'security/ir.model.access.csv',
        'views/th_user_view.xml',
    ],
    'license': "OPL-1",

    'auto_install': False,
    'application': True,
    'installable': True,

}
