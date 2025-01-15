
from odoo import fields, models, api, Command
import re
import unicodedata


class ProductCategory(models.Model):
    _inherit = "product.category"

    slug = fields.Char(string="Slug", default="slug")

    def _generate_slug(self, name):
        name = name.replace("đ", "d").replace("Đ", "d")
        slug = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
        slug = re.sub(r'[\W_]+', '-', slug.lower()).strip('-')
        return slug

    @api.onchange("name")
    def onchange_compute_slug(self):
        if self.name:
            self.slug = self._generate_slug(self.name)
