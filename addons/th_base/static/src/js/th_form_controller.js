// /** @odoo-module **/
// import FormController from "web.FormController";
// import config from 'web.config';
//
// FormController.include({
//     // Ẩn action menu form view
//     _getActionMenuItems: function (state) { 
//         if(config.isDebug()){
//             return this._super.apply(this, arguments);
//         }
//         else return null;
//     },
// });