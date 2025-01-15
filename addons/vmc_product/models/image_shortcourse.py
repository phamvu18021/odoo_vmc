from odoo import fields, models, api, Command


class ImageShortCourse(models.Model):
    _name = "image.shortcourse"
    _description = "Image for Short Course"

    name = fields.Char(string="Image Name")
    image = fields.Binary(string="Image")
