from odoo import fields, models, api, Command
import re
import unicodedata


def _generate_slug(name):
    name = name.replace("đ", "d").replace("Đ", "d")
    slug = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
    slug = re.sub(r'[\W_]+', '-', slug.lower()).strip('-')
    return slug


class ThTeacher(models.Model):
    _name = 'th.teacher'
    _description = 'Giáo viên'

    name = fields.Char(string="Tên giáo viên ", required=True)
    th_img_thumb = fields.Binary(string="Ảnh đại diện")
    th_img_banner_url = fields.Char("URL Ảnh đại diện", compute="_compute_img_banner_url", store=True)
    description = fields.Text(string="Mô tả")
    name_to_slug = fields.Char(string="Slug từ tên")

    @api.model
    def create(self, values):
        return super(ThTeacher, self).create(values)

    @api.depends('th_img_thumb')
    def _compute_img_banner_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for teacher in self:
            if teacher.th_img_thumb:
                teacher.th_img_banner_url = f"{base_url}/web/image/{teacher._name}/{teacher.id}/th_img_thumb"
            else:
                teacher.th_img_banner_url = False

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.name_to_slug = _generate_slug(self.name)
