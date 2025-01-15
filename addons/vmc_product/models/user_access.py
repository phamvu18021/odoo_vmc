from odoo import models, fields, api


class UserAccess(models.Model):
    _name = 'user.access'
    _description = 'User Access Record'

    name = fields.Char(string='Name', required=True)
    partner = fields.Many2one('res.partner', string='Partner', ondelete='set null')
    access_count = fields.Integer(string='Access Count', default=0)
