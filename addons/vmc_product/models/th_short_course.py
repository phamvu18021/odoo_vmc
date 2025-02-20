from odoo import api, fields, models
import re
import unicodedata


class ShortCourse(models.Model):
    _inherit = "product.template"
    slug_url = fields.Char('Slug URL', store="true")
    idWordPress = fields.Char(string='idWordPress', default='0')
    th_teacher_id = fields.Many2one('th.teacher', string="Giáo viên")
    time = fields.Char('Ngày ra mắt')
    duration = fields.Char('Thời lượng')
    description = fields.Text('Mô tả')
    th_img_thumb_url = fields.Char('Image URL', compute="_compute_img_thumb_url")
    image_shortcourse_url = fields.Char('Image ShortCourse URL', compute="_compute_image_shortcourse_url")

    name_to_slug = fields.Char(string="Slug từ tên")

    @api.model
    def create(self, values):
        record = super(ShortCourse, self).create(values)
        self.env['image.shortcourse'].create({
            'name': f"shortcourse_image_{record.id}",
            'image': record.image_512,
        })
        return record

    def write(self, vals):
        res = super(ShortCourse, self).write(vals)
        for record in self:
            # Tìm kiếm bản ghi tương ứng trong image.shortcourse
            image_shortcourse = self.env['image.shortcourse'].search(
                [('name', '=', f"shortcourse_image_{record.id}")], limit=1)

            if not image_shortcourse:
                # Nếu chưa có bản ghi trong image.shortcourse, tạo mới
                self.env['image.shortcourse'].create({
                    'name': f"shortcourse_image_{record.id}",
                    'image': record.image_512,
                })
            else:
                # Nếu đã có bản ghi, cập nhật ảnh nếu image_512 thay đổi
                if 'image_1920' in vals:
                    image_shortcourse.image = record.image_512
        return res

    @api.depends('image_512')
    def _compute_image_shortcourse_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            # Tìm kiếm record image_shortcourse tương ứng
            image_shortcourse = self.env['image.shortcourse'].search(
                [('name', '=', f"shortcourse_image_{record.id}")],
                limit=1
            )
            if image_shortcourse:
                # Tạo URL công khai cho image_shortcourse
                record.image_shortcourse_url = f"{base_url}/web/image?model=image.shortcourse&id={image_shortcourse.id}&field=image"
            else:
                record.image_shortcourse_url = False

    def _compute_img_thumb_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for shortcourse in self:
            if shortcourse.image_512:
                shortcourse.th_img_thumb_url = f"{base_url}/web/image?model=product.template&id={shortcourse.id}&field=image_512"
            else:
                shortcourse.th_img_thumb_url = "false"

    def open_create_wordpress_link(self, *args, **kwargs):
        base_url = 'http://localhost:10017/wp-admin/post-new.php?cat=7&idOdoo='
        random_part = self.id or ''
        full_url = f'{base_url}{random_part}'
        return {
            'type': 'ir.actions.act_url',
            'url': full_url,
            'target': 'new',
        }

    def open_edit_wordpress_link(self, *args, **kwargs):
        base_url = 'http://localhost:10017/wp-admin/post.php?post='
        random_part = self.idWordPress or ''
        idOdoo = self.id or ''
        full_url = f'{base_url}{random_part}&action=edit&idOdoo={idOdoo}'
        return {
            'type': 'ir.actions.act_url',
            'url': full_url,
            'target': 'new',
        }

    def _generate_slug(self, name):
        name = name.replace("đ", "d").replace("Đ", "d")
        slug = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
        slug = re.sub(r'[\W_]+', '-', slug.lower()).strip('-')
        return slug

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.name_to_slug = self._generate_slug(self.name)
