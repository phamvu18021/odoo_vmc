from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _, exceptions
from odoo.exceptions import ValidationError
import xmlrpc.client
from odoo.exceptions import UserError
import json


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # @api.model_create_multi
    # def create(self, values):
    #     # Call the original create method to create the sale order
    #     sale_order = super(SaleOrder, self).create(values)
    #     for vals in values:
    #         if vals.get('th_order_vmc_id') and not self._context.get('th_test_import', False):
    #             for rec in sale_order:
    #                 if rec.th_sale_order == 'apm':
    #                     rec.action_confirm()
    #     return sale_order
    #
    # def write(self, vals):
    #     res = super(SaleOrder, self).write(vals)
    #     for rec in self:
    #         if vals.get('th_status') and not self._context.get('th_test_import', False):
    #             rec.th_sync_status_sale_order()
    #         if rec.state == 'sale' and rec.order_line and rec.th_apm_id and not self._context.get('th_test_import', False):
    #             self.th_sync_order_vmc(rec)
    #     return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    free_product = fields.Boolean(string="Free Product", store=True)
    discount = fields.Float(
        string="Discount (%)",
        compute='_compute_discount',
        digits=(16, 3),
        store=True, readonly=False, precompute=True)

    @api.onchange('price_unit', 'discount')
    def _compute_price_reduce(self):
        for line in self:
            if line.reward_id:
                line.price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
            else:
                try:
                    line = line.with_company(line.company_id)
                    pricelist_price = line._get_pricelist_price()
                    line.price_reduce = pricelist_price
                except:
                    line.price_reduce = 0
