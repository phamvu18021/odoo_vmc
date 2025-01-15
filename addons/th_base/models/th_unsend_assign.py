from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class UnsendAssign(models.Model):
    _name = 'th.unsend.assign'
    _description = 'Không gửi mail phân công'


    th_model_id = fields.Many2one(comodel_name="ir.model", string="Model", required=1, ondelete="cascade")
    th_model_name = fields.Char(string="Model", related="th_model_id.model", store=True)

    @api.constrains('th_model_id')
    def _th_constaint_th_model_id(self):
        if any(self.search([('th_model_id', '=', rec.th_model_id.id), ('id', '!=', rec.id)]) for rec in self):
            raise ValidationError(_('Model đã tồn tại. Vui lòng kiểm tra lại'))
