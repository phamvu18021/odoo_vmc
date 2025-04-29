from odoo import models, fields
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


class FastAPISyncProductCategory(models.Model):
    _inherit = 'fastapi.endpoint'

    app = fields.Selection(
        selection_add=[('api_sync_product_category', 'SyncProductCategory API')],
        ondelete={'api_sync_product_category': 'cascade'}
    )

    def _get_fastapi_routers(self):
        routers = super()._get_fastapi_routers()
        if self.app == 'api_sync_product_category':
            fapi = FastAPI()
            fapi.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],  # Cho phép tất cả các nguồn
                allow_credentials=True,
                allow_methods=["*"],  # Cho phép tất cả các phương thức
                allow_headers=["*"],  # Cho phép tất cả các headers
            )
            from ..routers import sync_product_category
            routers.extend([sync_product_category.router])
            fapi.include_router(sync_product_category.router)
        return routers
