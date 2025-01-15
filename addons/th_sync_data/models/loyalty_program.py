from odoo import api, fields, models, _
from xml.etree import ElementTree as etree
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
import xmlrpc.client

class LoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'
    _description = "Mã giảm giá"

    start_date = fields.Datetime(string="Start Date")
    date_to = fields.Date(string="Validity")
    thc_date_to = fields.Datetime(string="Validity")
    program_type = fields.Selection(selection='_get_new_question_type', default='promotion', required=True)
    is_preorder = fields.Boolean("Preorder", store=True)
    th_samp_discount_loyalty_id = fields.Integer(string='ID mã giảm giá samP')

    @api.constrains('thc_date_to')
    def _constrain_thc_date_to(self):
        for record in self:
            if record.thc_date_to:
                record.date_to = record.thc_date_to.date()

    @api.model
    def _get_new_question_type(self):
        selection = [('promotion', 'Khuyến mại'), ('promo_code', 'Mã giảm giá'), ('buy_x_get_y', 'Mua X tặng Y')]
        return selection

    def th_sync_loyalty_program(self):
        return self.env['loyalty.program'].search([]).ids


class LoyaltyReward(models.Model):
    _inherit = 'loyalty.reward'
    _description = ""

    condition_des = fields.Text(string="Condition Description", required=True)
    reward_product_category = fields.Many2one("product.category", string="Categories")
    th_samp_reward_loyalty_id = fields.Integer(string="ID Reward samP")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            program = self.env['loyalty.program'].browse(vals.get('program_id', []))
            if program and program.program_type != 'buy_x_get_y' and vals.get('discount_max_amount') == 0:
                raise UserError('Vui lòng không thiết lập giá trị Giảm giá tối đa bằng 0 cho Chiết khấu trong Phần thưởng !')
            if not vals.get('condition_des'):
                raise UserError('Vui lòng thêm Mô tả điều kiện trong Phần thưởng !')
        res = super().create(vals_list)
        res._create_missing_discount_line_products()
        return res


class LoyaltyRule(models.Model):
    _inherit = 'loyalty.rule'
    _description = ""

    th_samp_rule_loyalty_id = fields.Integer(string="ID Reward samP")


class SaleLoyaltyRewardWizard(models.TransientModel):
    _inherit = 'sale.loyalty.reward.wizard'

    selected_reward_id = fields.Many2one('loyalty.reward',
                                         domain="[('id', 'in', reward_ids),"
                                                "'|', ('program_id.start_date', '<=', datetime.datetime.now()), ('program_id.start_date', '=', False),"
                                                "'|', ('program_id.thc_date_to', '>=', datetime.datetime.now()), ('program_id.thc_date_to', '=', False)]")
