from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _, exceptions
from odoo.exceptions import ValidationError
import xmlrpc.client
from odoo.exceptions import UserError
import json


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    th_e2_product_price_list_id = fields.Integer("ID bảng giá e2", copy=False)
    th_is_short_pricelist = fields.Boolean('Là bảng giá ngắn hạn', copy=False)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'
