{
    'name': 'Vmc Product',
    'summary': "Vmc Product",
    'description': """
     Vmc Product.
    ========================
    """,

    'author': 'AUM it',
    'website': '',
    'category': 'AUM Business System/ Vmc Product',
    'version': '1.3',
    'depends': ['base', 'product', 'sale', 'stock', 'web_editor'],
    'data': [
        'security/ir.model.access.csv',
        'views/th_short_course_view.xml',
        'views/image_shortcourse_views.xml',
        'views/user_access_view.xml',
        'views/th_product_tags.xml',
        'views/th_teacher_view.xml',
        'views/th_teacher_views.xml',
        'views/product_category_views.xml',
        'views/product_category_group_menu.xml',
        'views/product_category_group_views.xml',
        'views/loyalty_reward_views.xml',
        'views/th_sale_order_view.xml',
        'views/menus.xml',

    ],

    'license': "OPL-1",

    'auto_install': False,
    'application': True,
    'installable': True,

    'images': ['static/description/banner.png'],
}
