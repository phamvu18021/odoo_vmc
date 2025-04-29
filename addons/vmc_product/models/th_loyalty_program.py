from odoo import models, fields

class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    id_ee = fields.Integer(string="ID CTKM ở EE")
