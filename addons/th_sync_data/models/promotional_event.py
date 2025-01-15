from odoo import api, fields, models, _
from pytz import timezone
from odoo.exceptions import ValidationError
import xmlrpc.client


class PromotionalEvent(models.Model):

    _name = "th.promotional.event"

    name = fields.Char("Name", store=True)
    description = fields.Char("Description", store=True)
    active_voucher = fields.Boolean("Active", store=True)
    voucher = fields.Many2many('loyalty.program', 'loyalty_event_rel', 'th_promotional_event_id', 'loyalty_program_id', string="Voucher", store=True)
    th_samp_promotional_event_id = fields.Integer(string='ID chương trình chuyến mãi samp')

    # @api.model
    # def create(self, values):
    #     res = super(PromotionalEvent, self).create(values)
    #     if not self._context.get('th_test_import', False):
    #         self.th_synchronized_promotional_event(res, create=True)
    #     return res
    #
    # def write(self, values):
    #     res = super(PromotionalEvent, self).write(values)
    #     if res and not self._context.get('th_test_import', False):
    #         self.th_synchronized_promotional_event(self, update=True)
    #
    # def th_synchronized_promotional_event(self, records, update=None, create=None):
    #     data_to_send = False
    #     server_api = self.env['th.api.server'].search([('state', '=', 'deploy'), ('th_type', '=', 'vmc')],
    #                                                   limit=1,
    #                                                   order='id desc')
    #     try:
    #         if not server_api:
    #             raise ValidationError('Không tìm thấy server!')
    #         result_apis = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_api.th_url_api))
    #         db = server_api.th_db_api
    #         uid_api = server_api.th_uid_api
    #         password = server_api.th_password
    #         for record in records:
    #             voucher = []
    #             for vou in record.voucher:
    #                 if vou.th_2e_discount_loyalty_id != 0:
    #                     voucher.append(vou.th_2e_discount_loyalty_id)
    #             data_to_send = {
    #                 'name': record.name,
    #                 'description': record.description,
    #                 'active_voucher': record.active_voucher,
    #                 'voucher': voucher if voucher != [] else False,
    #             }
    #
    #             if create:
    #                 category_id = result_apis.execute_kw(db, uid_api, password, 'th.promotional.event', 'create',
    #                                                      [data_to_send])
    #                 record.write({'th_2e_promotional_event_id': category_id})
    #             elif update:
    #                 result_apis.execute_kw(db, uid_api, password, 'th.promotional.event', 'write',
    #                                        [[record.th_2e_promotional_event_id], data_to_send])
    #     except Exception as e:
    #         print(e)
    #         self.env['th.log.api'].create({
    #             'state': 'error',
    #             'th_model': str(self._name),
    #             'th_description': str(e),
    #             'th_record_id': str(records.id),
    #             'th_input_data': str(data_to_send),
    #             'th_function_call': str('th_synchronized_promotional_event'),
    #         })
    #         return
    #
    # def th_sync_promotional_event(self):
    #     return self.env['th.promotional.event'].search([]).ids