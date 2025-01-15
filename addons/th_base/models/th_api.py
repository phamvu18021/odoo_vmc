import xmlrpc

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


READONLY_STATES = {
    'deploy': [('readonly', True)],
    'close': [('readonly', True)],
}
th_type = [('aff', 'Affiliate'), ('samp', 'Sambala production'), ('vmc', 'VMC'), ('b2c', 'B2C'), ('ete', 'Eteaching')]
state = [('draft', 'Nháp'), ('deploy', 'Triển khai'), ('close', 'Đóng')]


class ThApiServer(models.Model):
    _name = 'th.api.server'
    _description = "Set up api server"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'th_url_api'

    th_url_api = fields.Char('URL server', required=1, states=READONLY_STATES)
    th_user_api = fields.Char('Tài khoản sử dụng API', required=1, states=READONLY_STATES)
    th_partner_api_id = fields.Char('ID Liên hệ')
    th_password = fields.Char('Key API(password)', required=1, states=READONLY_STATES)
    th_db_api = fields.Char('Cơ sở dữ liệu', required=1, states=READONLY_STATES)
    th_uid_api = fields.Char('Tài khoản kết nối', copy=0)
    state = fields.Selection(selection=state, tracking=True, default='draft')
    th_description = fields.Text("Mô tả")
    th_type = fields.Selection(selection=th_type, tracking=True, required=1, string='Loại', states=READONLY_STATES)

    def action_test_server(self):
        for rec in self:
            try:
                common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(rec.th_url_api))
                result_apis = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(rec.th_url_api))
                common.version()
                user_id = common.authenticate(rec.th_db_api, rec.th_user_api, rec.th_password, {})
                partner_id = False
                if not user_id:
                    raise ValidationError(_(f'Không tìm thấy tài khoản để kết nối tới server!'))
                if rec.th_type == 'aff':
                    # các module yêu cầu check_access_rights trước để ko tránh bị lỗi khi call api
                    # th.opportunity.ctv
                    # res.partner
                    # res.users
                    # th.pricelist
                    # th.warehouse

                    res_partner = result_apis.execute_kw(rec.th_db_api, user_id, rec.th_password, 'res.partner', 'check_access_rights', ['read'], {'raise_exception': False})
                    if not res_partner:
                        raise ValidationError('Tài khoản không có quyền truy cập module Liên hệ(res.partner)!')

                    partner_id = result_apis.execute_kw(rec.th_db_api, user_id, rec.th_password, 'res.users', 'read', [user_id], {'fields': [('partner_id')]})

                    res_user = result_apis.execute_kw(rec.th_db_api, user_id, rec.th_password, 'res.users', 'check_access_rights', ['read'], {'raise_exception': False})
                    if not res_user:
                        raise ValidationError('Tài khoản không có quyền truy cập module Tài khoản(res.users)!')

                    # th_opportunity_ctv = result_apis.execute_kw(rec.th_db_api, user_id, rec.th_password, 'th.opportunity.ctv', 'check_access_rights', ['read'], {'raise_exception': False})
                    # if not th_opportunity_ctv:
                    #     raise ValidationError(
                    #         'Tài khoản không có quyền truy cấp module Cơ hội của CTV(th.opportunity.ctv)!')

                if rec.th_type == 'vmc':
                    if not result_apis.execute_kw(rec.th_db_api, user_id, rec.th_password, 'sale.order', 'check_access_rights', ['read'], {'raise_exception': False}):
                        raise ValidationError('Tài khoản không có quyền truy cấp module bán hàng(sale.order)!')

            except Exception as e:
                if 'Object' in str(e) and "doesn't exist" in str(e):
                    raise ValidationError(
                        f"Bảng '{e.faultString.split(' ')[1]}' không tồn tại trong cơ sở dữ liệu {self.th_db_api}")
                raise ValidationError(e)

            rec.write({'th_uid_api': user_id, 'th_partner_api_id': partner_id[0]['partner_id'][0] if partner_id else False})

        message = _("Kết nối thành công")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_deploy(self):
        if self.state != 'draft':
            raise ValidationError(_("Trạng thái phải là nháp!"))
        if not self.th_uid_api:
            self.action_test_server()

        if self.search([('id', '!=', self.id), ('state', '=', 'deploy'), ('th_type', '=', self.th_type)]):
            raise ValidationError(_('Không thể có 2 server api cùng loại được triển khai!'))

        self.write({
            'state': 'deploy'
        })

    def action_draft(self):
        if self.state != 'close':
            raise ValidationError(_("Trạng thái phải là đóng"))
        self.write({
            'state': 'draft'
        })

    def action_close(self):
        if self.state != 'deploy':
            raise ValidationError(_("Trạng thái phải là triển khai"))
        self.write({
            'state': 'close'
        })

    def write(self, values):
        if values.get('th_url_api', False) \
                or values.get('th_user_api', False) or values.get('th_password', False) \
                or values.get('th_db_api', False) or values.get('th_type', False):
            values['th_uid_api'] = False
        return super(ThApiServer, self).write(values)
