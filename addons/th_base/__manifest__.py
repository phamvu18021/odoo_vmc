{
    'name': 'ABS Base',
    'author': "TH Company",
    'summary': 'ABS Base',
    'category': 'AUM Business System/ Base',
    'website': 'https://aum.edu.vn/',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'report_xlsx',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/actions.xml',
        'report/th_report_data.xml',
        'views/th_api.xml',
        'views/res_config_settings.xml',
        'views/th_unsend_assign_view.xml',
        'wizard/th_wizard_import.xml',
        'wizard/th_import_custom.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'th_base/static/src/scss/change_css_base.scss',
            'th_base/static/src/js/import_action.js',
            'th_base/static/src/js/th_domain_field.js',
            'th_base/static/src/xml/th_domain_field.xml',
        ],
    },
    'installable': True,
    'auto_install': True,
}
