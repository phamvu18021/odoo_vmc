from odoo import models, fields


class LoyaltyReward(models.Model):
    _inherit = "loyalty.reward"

    reward_id_sam = fields.Char(string="Reward ID SAM")
    conditions_description = fields.Char(string="Mô tả điều kiện để sử dụng")
