import requests
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError
from typing import Optional
from odoo import _

_logger = logging.getLogger(__name__)


def get_ecm_category_id(env, external_id: int) -> int:
    category = env["product.category"].sudo().search([("categ_id_ee", "=", external_id)], limit=1)
    if not category:
        return
    return category.id


def get_ecm_product_ids(env, external_ids: list) -> list:
    if not external_ids:
        return []
    product_ids = []
    for ext_id in external_ids:
        product = env["product.template"].sudo().search([("product_id_ee", "=", ext_id)], limit=1)
        if not product:
            raise UserError(_("Product with product_id_ee %s not found.") % ext_id)
        product_ids.append(product.id)
    return product_ids


def get_ecm_reward_product_id(env, external_id: int) -> int:
    product = env["product.template"].sudo().search([("product_id_ee", "=", external_id)], limit=1)
    if not product:
        raise UserError(_("Reward Product with product_id_ee %s not found.") % external_id)
    return product.id


def get_parent_category(env, parent_ext_id: str) -> Optional[int]:
    parent_cat = env["product.category"].sudo().search([("categ_id_ee", "=", parent_ext_id)], limit=1)
    return parent_cat.id if parent_cat else None


class SyncConfig(models.Model):
    _name = 'sync.config'
    _description = 'Configuration for Data Synchronization'

    name = fields.Char(string="Configuration Name", required=True)
    model_name = fields.Selection([
        ('loyalty.program', 'Loyalty Program'),
        ('product.template', 'Product Template'),
        ('product.category', 'Product Category'),
        ('sale.order', 'Sale Order')
    ], string="Model Name", required=True, help="Select the model to sync")
    sync_url = fields.Char(string="Sync URL", required=True)
    auth_token = fields.Char(string="Auth Token")
    active = fields.Boolean(default=True)

    time_range_value = fields.Integer(string="Khoảng thời gian", default=2,
                                      help="Số lượng đơn vị thời gian để kiểm tra create/write date")
    time_range_unit = fields.Selection([
        ("seconds", "Giây"),
        ("minutes", "Phút"),
        ("hours", "Giờ"),
        ("days", "Ngày"),
    ], string="Đơn vị thời gian", default="hours", help="Đơn vị thời gian để tính toán khoảng thời gian gần đây")

    def _get_timedelta(self):
        unit = self.time_range_unit
        value = self.time_range_value
        if unit == "seconds":
            return timedelta(seconds=value)
        elif unit == "minutes":
            return timedelta(minutes=value)
        elif unit == "hours":
            return timedelta(hours=value)
        elif unit == "days":
            return timedelta(days=value)
        return timedelta(hours=2)  # fallback

    @api.model
    def cron_sync_all(self):
        configs = self.search([("active", "=", True)])
        if not configs:
            _logger.warning("No active sync configuration found.")
            return True
        for config in configs:
            headers = {}
            if config.auth_token:
                headers["Authorization"] = f"Bearer {config.auth_token}"
            try:
                response = requests.get(config.sync_url, headers=headers, timeout=30)
                if response.status_code != 200:
                    _logger.error("Remote API for %s returned status code %s", config.name, response.status_code)
                    continue
                data = response.json()
            except Exception as e:
                _logger.exception("Error calling remote API for %s: %s", config.name, e)
                continue

            if config.model_name == "loyalty.program":
                config._sync_loyalty_programs(data)
            elif config.model_name == "product.template":
                config._sync_product_templates(data)
            elif config.model_name == "product.category":
                config._sync_product_category(data)
            elif config.model_name == "sale.order":
                config._sync_sale_order(data)
            else:
                _logger.warning("No sync function defined for model: %s", config.model_name)
        return True

    def _create_or_update_program(self, prog_data, update=False):
        env = self.env
        converted_rules = []
        for rule in prog_data.get("rule_ids", []):
            internal_category_id = None
            if rule.get("product_category_id") is not None:
                try:
                    internal_category_id = get_ecm_category_id(env, rule.get("product_category_id"))
                except ValueError as e:
                    _logger.warning("Skipping rule due to: %s", e)
                    continue
            internal_product_ids = get_ecm_product_ids(env, rule.get("product_ids"))
            converted_rules.append({
                "product_category_id": internal_category_id,
                "product_ids": [(6, 0, internal_product_ids)],
                "minimum_qty": rule.get("minimum_qty"),
                "minimum_amount": rule.get("minimum_amount"),
                "product_domain": rule.get("product_domain"),
                "reward_point_mode": rule.get("reward_point_mode"),
                "code": rule.get("code"),
                "reward_point_split": rule.get("reward_point_split"),
                "reward_point_amount": rule.get("reward_point_amount"),
            })

        converted_rewards = []
        for reward in prog_data.get("reward_ids", []):
            rp_internal = None
            if reward.get("reward_type") == "product":
                if not reward.get("reward_product_id"):
                    _logger.warning("Skipping reward because reward_product_id is missing.")
                    continue
                try:
                    rp_internal = get_ecm_reward_product_id(env, reward.get("reward_product_id"))
                except ValueError as e:
                    _logger.warning("Skipping reward due to: %s", e)
                    continue
                discount_mode = "percent"
                discount = 0
                discount_max_amount = 0
            else:
                discount_mode = reward.get("discount_mode")
                discount = reward.get("discount")
                discount_max_amount = reward.get("discount_max_amount")
            converted_rewards.append({
                "reward_type": reward.get("reward_type"),
                "discount_mode": discount_mode,
                "discount": discount,
                "discount_max_amount": discount_max_amount,
                "discount_applicability": reward.get("discount_applicability"),
                "discount_product_domain": reward.get("discount_product_domain"),
                "reward_product_id": rp_internal,
                "reward_product_qty": reward.get("reward_product_qty"),
                "required_points": reward.get("required_points"),
            })

        values = {
            "id_ee": prog_data.get("id_ee"),
            "name": prog_data.get("name"),
            "program_type": prog_data.get("program_type"),
            "portal_point_name": prog_data.get("portal_point_name"),
            "date_to": prog_data.get("date_to"),
            "max_usage": prog_data.get("max_usage"),
            "company_id": prog_data.get("company_id"),
            "available_on": prog_data.get("available_on"),
            "trigger": prog_data.get("trigger"),
            "rule_ids": [(0, 0, rule) for rule in converted_rules],
            "reward_ids": [(0, 0, reward) for reward in converted_rewards],
        }
        if update:
            record = env["loyalty.program"].sudo().search([("id_ee", "=", prog_data.get("id_ee"))], limit=1)
            record.sudo().write(values)
        else:
            env["loyalty.program"].sudo().create(values)

    def _sync_sale_order(self, orders_data):
        now = datetime.now()
        time_window = self._get_timedelta()
        two_minutes = timedelta(minutes=2)
        created = 0
        updated = 0

        for order_data in orders_data:
            try:
                order_create_date = fields.Datetime.from_string(order_data.get("create_date"))
                order_write_date = fields.Datetime.from_string(order_data.get("write_date"))
            except Exception as e:
                _logger.warning("Invalid date format for order %s: %s", order_data.get("order_id_ee"), e)
                continue

            order_id_ee = order_data.get("order_id_ee")
            if not order_id_ee:
                continue

            # Tìm đơn hàng trong Odoo
            existing_order = self.env["sale.order"].sudo().search([("order_id_ee", "=", order_id_ee)], limit=1)

            if order_create_date and order_create_date >= now - time_window and not existing_order:
                # Tạo mới đơn hàng nếu chưa có
                partner_id = self._get_partner_id(order_data.get("partner_email"))
                order = self.env["sale.order"].sudo().create({
                    "partner_id": partner_id,
                    "order_id_ee": order_id_ee,
                    "state": "draft",  # Đặt trạng thái ban đầu là draft
                    "date_order": order_create_date,
                })
                self._sync_order_lines(order, order_data.get("items"))
                created += 1
            elif order_write_date and order_write_date >= now - time_window:
                if not existing_order:
                    # Tạo mới đơn hàng nếu chưa có
                    partner_id = self._get_partner_id(order_data.get("partner_email"))
                    order = self.env["sale.order"].sudo().create({
                        "partner_id": partner_id,
                        "order_id_ee": order_id_ee,
                        "state": "draft",
                        "date_order": order_create_date,
                    })
                    self._sync_order_lines(order, order_data.get("items"))
                    created += 1
                else:
                    # Cập nhật đơn hàng nếu có sự thay đổi
                    existing_write_date = fields.Datetime.from_string(existing_order.write_date)
                    if abs(order_write_date - existing_write_date) > two_minutes:
                        # Cập nhật các thông tin đơn hàng và trạng thái
                        partner_id = self._get_partner_id(order_data.get("partner_email"))
                        existing_order.sudo().write({
                            "partner_id": partner_id,
                            "state": order_data.get("state", existing_order.state),
                            "date_order": order_write_date,
                        })
                        # Cập nhật các dòng sản phẩm của đơn hàng
                        self._sync_order_lines(existing_order, order_data.get("items"))
                        updated += 1

            # Áp dụng chương trình khuyến mãi nếu có
            if order_data.get("promotion_id_ee"):
                self._apply_promotion(order, order_data.get("promotion_id_ee"))

        _logger.info("Sync Sale Orders: %s created, %s updated.", created, updated)

    def _get_partner_id(self, partner_email):
        # Tìm khách hàng theo email
        partner = self.env["res.partner"].sudo().search([("email", "=", partner_email)], limit=1)
        if not partner:
            partner = self.env["res.partner"].sudo().create({
                "name": partner_email,  # Tên khách hàng là email nếu không tìm thấy
                "email": partner_email,
            })
        return partner.id

    def _sync_order_lines(self, order, items_data):
        # Xóa tất cả các dòng sản phẩm hiện tại trong đơn hàng
        order.order_line.sudo().unlink()

        # Thêm sản phẩm mới vào đơn hàng
        for item in items_data:
            product = self.env["product.template"].sudo().search([("product_id_ee", "=", item.get("product_id_ee"))],
                                                                 limit=1)
            if not product:
                _logger.warning("Product %s not found. Skipping...", item.get("product_id_ee"))
                continue

            self.env["sale.order.line"].sudo().create({
                "order_id": order.id,
                "product_id": product.id,
                "product_uom_qty": item.get("quantity"),
                "price_unit": item.get("price"),
                "name": product.name
            })

    def _apply_promotion(self, order, promotion_id_ee):
        # Tìm chương trình khuyến mãi trong Odoo
        program = self.env["loyalty.program"].sudo().search([("id_ee", "=", promotion_id_ee)], limit=1)

        if not program:
            _logger.warning("Promotion program with id_ee %s not found. Skipping...", promotion_id_ee)
            return

        # Cập nhật các chương trình khuyến mãi có thể áp dụng cho đơn hàng
        order._update_programs_and_rewards()
        claimable_rewards = order._get_claimable_rewards() or {}

        selected_reward = None
        selected_coupon = None

        # Kiểm tra và áp dụng chương trình khuyến mãi
        if program.program_type == "promo_code":
            for coupon, rewards in claimable_rewards.items():
                for reward in rewards:
                    if reward.program_id.id == program.id:
                        selected_reward = reward
                        selected_coupon = coupon
                        break
                if selected_reward:
                    break
            if not selected_reward:
                order._remove_promotion_lines()
                wizard = self.env["sale.loyalty.coupon.wizard"].sudo().create({
                    "order_id": order.id,
                    "coupon_code": program.rule_ids[0].code if program.rule_ids else ""
                })
                wizard.action_apply()
        else:
            for coupon, rewards in claimable_rewards.items():
                for reward in rewards:
                    if reward.program_id.id == program.id:
                        selected_reward = reward
                        selected_coupon = coupon
                        break
                if selected_reward:
                    break

            if selected_reward:
                order._apply_program_reward(selected_reward, selected_coupon)

    def _sync_loyalty_programs(self, programs_data):
        now = datetime.now()
        time_window = self._get_timedelta()
        two_minutes = timedelta(minutes=2)
        created = 0
        updated = 0

        for prog in programs_data:
            try:
                prog_create_date = fields.Datetime.from_string(prog.get("create_date"))
                prog_write_date = fields.Datetime.from_string(prog.get("write_date"))
            except Exception as e:
                _logger.warning("Invalid date format for program %s: %s", prog.get("id_ee"), e)
                continue

            id_ee = prog.get("id_ee")
            existing = self.env["loyalty.program"].sudo().search([("id_ee", "=", id_ee)], limit=1)

            if prog_create_date and prog_create_date >= now - time_window and not existing:
                self._create_or_update_program(prog, update=False)
                created += 1
            elif prog_write_date and prog_write_date >= now - time_window:
                if not existing:
                    self._create_or_update_program(prog, update=False)
                    created += 1
                else:
                    existing_write = fields.Datetime.from_string(existing.write_date)
                    if abs(prog_write_date - existing_write) > two_minutes:
                        self._create_or_update_program(prog, update=True)
                        updated += 1

        _logger.info("Sync Loyalty Programs: %s created, %s updated.", created, updated)

    def _sync_product_templates(self, products_data):
        now = datetime.now()
        time_window = self._get_timedelta()
        two_minutes = timedelta(minutes=2)
        created = 0
        updated = 0
        external_ids = set()

        for product in products_data:
            try:
                create_date = fields.Datetime.from_string(product.get("create_date"))
                write_date = fields.Datetime.from_string(product.get("write_date"))
            except Exception as e:
                _logger.warning("Invalid date format for product %s: %s", product.get("product_id_ee"), e)
                continue

            product_id_ee = product.get("product_id_ee")
            if not product_id_ee:
                continue

            external_ids.add(product_id_ee)

            existing = self.env["product.template"].sudo().search([("product_id_ee", "=", product_id_ee)], limit=1)

            if create_date and create_date >= now - time_window and not existing:
                categ_id = get_ecm_category_id(self.env, product.get("categ_id_ee")) if product.get(
                    "categ_id_ee") else 1
                self.env["product.template"].sudo().create({
                    "product_id_ee": product_id_ee,
                    "name": product.get("name"),
                    "list_price": product.get("list_price"),
                    "categ_id": categ_id,
                    "default_code": product.get("default_code_ee"),
                })
                created += 1
            elif write_date and write_date >= now - time_window:
                if not existing:
                    categ_id = get_ecm_category_id(self.env, product.get("categ_id_ee")) if product.get(
                        "categ_id_ee") else 1
                    self.env["product.template"].sudo().create({
                        "product_id_ee": product_id_ee,
                        "name": product.get("name"),
                        "list_price": product.get("list_price"),
                        "categ_id": categ_id,
                        "default_code": product.get("default_code_ee")
                    })
                    created += 1
                else:
                    existing_write = fields.Datetime.from_string(existing.write_date)
                    if abs(write_date - existing_write) > two_minutes:
                        categ_id = get_ecm_category_id(self.env, product.get("categ_id_ee")) if product.get(
                            "categ_id_ee") else 1
                        existing.sudo().write({
                            "name": product.get("name"),
                            "list_price": product.get("list_price"),
                            "categ_id": categ_id,
                            "default_code": product.get("default_code_ee")
                        })
                        updated += 1

        # Deactivate old products not in the incoming list
        if external_ids:
            old_products = self.env["product.template"].sudo().search(
                [("product_id_ee", "not in", list(external_ids)), ("active", "=", True)])
            old_products.sudo().write({"active": False})

        _logger.info("Sync Product Templates: %s created, %s updated, %s deactivated.", created, updated,
                     len(old_products))
        return True

    def _sync_product_category(self, categories_data):
        now = datetime.now()
        time_window = self._get_timedelta()
        two_minutes = timedelta(minutes=2)
        created = 0
        updated = 0

        for cat in categories_data:
            try:
                cat_create_date = fields.Datetime.from_string(cat.get("create_date"))
                cat_write_date = fields.Datetime.from_string(cat.get("write_date"))
            except Exception as e:
                _logger.warning("Invalid date format for category %s: %s", cat.get("categ_id_ee"), e)
                continue

            ext_id = cat.get("categ_id_ee")
            if not ext_id:
                continue

            existing = self.env["product.category"].sudo().search([("categ_id_ee", "=", ext_id)], limit=1)

            if cat_create_date and cat_create_date >= now - time_window and not existing:
                parent_id = None
                if cat.get("categ_parent_id_ee"):
                    parent_id = get_parent_category(self.env, cat.get("categ_parent_id_ee"))
                self.env["product.category"].sudo().create({
                    "categ_id_ee": ext_id,
                    "name": cat.get("categ_name_ee"),
                    "parent_id": parent_id,
                })
                created += 1
            elif cat_write_date and cat_write_date >= now - time_window:
                if not existing:
                    parent_id = None
                    if cat.get("categ_parent_id_ee"):
                        parent_id = get_parent_category(self.env, cat.get("categ_parent_id_ee"))
                    self.env["product.category"].sudo().create({
                        "categ_id_ee": ext_id,
                        "name": cat.get("categ_name_ee"),
                        "parent_id": parent_id,
                    })
                    created += 1
                else:
                    existing_write = fields.Datetime.from_string(existing.write_date)
                    if abs(cat_write_date - existing_write) > two_minutes:
                        parent_id = None
                        if cat.get("categ_parent_id_ee"):
                            parent_id = get_parent_category(self.env, cat.get("categ_parent_id_ee"))
                        existing.sudo().write({
                            "name": cat.get("categ_name_ee"),
                            "parent_id": parent_id,
                        })
                        updated += 1

        _logger.info("Sync Product Categories: %s created, %s updated.", created, updated)
        return True
