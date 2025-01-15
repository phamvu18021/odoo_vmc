import json
import xmlrpc.client
from odoo import api, fields, models, _, Command
from odoo.http import request
import json
from odoo.exceptions import ValidationError
import math
import requests
from datetime import datetime
from datetime import timedelta


class ProductTemplate(models.Model):
    _inherit = "product.template"

    video = fields.Char(string='Link youtube', store=True)
    combo_list = fields.One2many('product.combo', 'product_template_id', string="combo List")
    preorder = fields.Datetime("Preorder")
    th_samp_product_temp_id = fields.Integer("ID sản phẩm samP", copy=False)

    def _group_expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.model
    def get_import_templates(self):
        res = super(ProductTemplate, self).get_import_templates()
        return [{
            'label': _('Import Template for Products'),
            'template': '/th_sync_data/static/template/Product_template.xlsx'
        }]

    @api.constrains('default_code')
    def check_duplicate_default_code(self):
        if any([self.env['product.template'].search([('id', '!=', rec.id), ('default_code', '=', rec.default_code), ('default_code', '!=', False)]) for rec in self]):
            raise ValidationError(_("Mã đã bị trùng!"))

    @api.model
    def create(self, values):
        # Add code here
        return super(ProductTemplate, self).create(values)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    display_name = fields.Char(string="Display Name")
    th_2e_id = fields.Integer(string="Mã danh múc sản phẩm 2e")
    th_category_ete_id = fields.Integer(string="Mã danh mục sản phẩm ete")

    @api.model
    def name_get(self):
        result = []
        for record in self:
            try:
                if record.parent_id.display_name:
                    record.display_name = record.parent_id.display_name + ' / ' + record.name
                else:
                    record.display_name = record.name
                result.append((record.id, record.display_name))
            except Exception as e:
                print(e)
                record.display_name = record.name
                result.append((record.id, record.display_name))
        return result


class ProductProduct(models.Model):
    _inherit = 'product.product'

    th_samp_product_pro_id = fields.Integer("ID biến thể sản phẩm samP", copy=False)


class ProductCombo(models.Model):
    _inherit = 'product.combo'

    th_samp_product_combo_id = fields.Integer("ID combo sản phẩm samP", copy=False)


class ProductTags(models.Model):
    _inherit = 'product.tag'

    th_samp_tag_id = fields.Integer(string="Mã danh múc sản phẩm samP", copy=False)
