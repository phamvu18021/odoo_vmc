from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    customer_payment_confirmed = fields.Boolean(string="Khách hàng đã xác nhận thanh toán")

    def _remove_promotion_lines(self):
        """Xóa tất cả dòng sản phẩm được thêm vào từ chương trình khuyến mãi"""
        promotion_lines = self.order_line.filtered(
            lambda line: line.is_reward_line or line.discount > 0 or line.price_unit == 0
        )
        if promotion_lines:
            promotion_lines.unlink()
