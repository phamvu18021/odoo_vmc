from odoo import models, fields, api
import re
import unicodedata


class ProductCategory(models.Model):
    _inherit = "product.category"

    slug = fields.Char(string="Slug", default="slug")
    categ_id_ee = fields.Integer(string="ID Danh mục EE")

    sequence = fields.Integer(
        string="Thứ tự hiển thị",
        default=10,
        help="Dùng để sắp xếp danh mục trên frontend"
    )
    def _generate_slug(self, name):
        name = name.replace("đ", "d").replace("Đ", "d")
        slug = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
        slug = re.sub(r'[\W_]+', '-', slug.lower()).strip('-')
        return slug

    @api.onchange("name")
    def onchange_compute_slug(self):
        if self.name:
            self.slug = self._generate_slug(self.name)
