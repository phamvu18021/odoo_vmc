from odoo import api, fields, models

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'


    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        if self.env['th.unsend.assign'].sudo().search([('th_model_name', '=', self._name)]):
            return []
        else:
            return super(MailThread, self)._message_auto_subscribe_followers(updated_values, default_subtype_ids)