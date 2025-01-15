odoo.define('th_check_import.import', function (require) {
    "use strict";
    const BaseImport = require('base_import.import');

    BaseImport.DataImport.include({
        call_import: function (kwargs) {
            // this.parent_context = {th_test_import: kwargs['dryrun']}
            if(typeof(this.parent_context) == 'object')
            {
                this.parent_context['th_test_import'] = kwargs['dryrun']
            }

            return this._super.apply(this, arguments);
        },
    });

});


