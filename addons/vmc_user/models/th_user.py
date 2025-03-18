from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string="Giới tính", default="male")
    age = fields.Integer(string="Tuổi")
    password = fields.Char(string="Mật khẩu", help="User's password for authentication.")
    status = fields.Boolean(string="Trạng thái", default=False)
    shortcourse_ids = fields.One2many(
        'partner.shortcourse.rel',
        'partner_id',
        string="Short Courses"
    )


class PartnerShortCourseRel(models.Model):
    _name = 'partner.shortcourse.rel'
    _description = 'Partner ShortCourse Relation'

    partner_id = fields.Many2one('res.partner', string="Partner")
    shortcourse_id = fields.Many2one('product.template', string="Short Course")
    quantity = fields.Integer(string="Số lượng", default=1)
