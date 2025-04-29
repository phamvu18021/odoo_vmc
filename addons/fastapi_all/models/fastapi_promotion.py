from odoo import models, fields
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


class FastAPIPromotion(models.Model):
    _inherit = 'fastapi.endpoint'

    app = fields.Selection(
        selection_add=[('api_promotion', 'Promotion API')],
        ondelete={'api_promotion': 'cascade'}
    )

    def _get_fastapi_routers(self):
        routers = super()._get_fastapi_routers()
        if self.app == 'api_promotion':
            fapi = FastAPI()
            fapi.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],  # Cho phép tất cả các nguồn
                allow_credentials=True,
                allow_methods=["*"],  # Cho phép tất cả các phương thức
                allow_headers=["*"],  # Cho phép tất cả các headers
            )
            from ..routers import promotion
            routers.extend([promotion.router])
            fapi.include_router(promotion.router)
        return routers
