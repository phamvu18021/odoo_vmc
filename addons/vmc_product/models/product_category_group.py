from odoo import models, fields

class ProductCategoryGroup(models.Model):
    _name = 'product.category.group'
    _description = 'Nhóm danh mục sản phẩm'

    name = fields.Char(string="Tên nhóm", required=True)
    category_ids = fields.Many2many('product.category', string="Danh mục thuộc nhóm")
