from odoo import models, fields
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


class FastAPISyncOrder(models.Model):
    _inherit = 'fastapi.endpoint'

    app = fields.Selection(
        selection_add=[('api_sync_order', 'Sync Order API')],
        ondelete={'api_sync_order': 'cascade'}
    )

    def _get_fastapi_routers(self):
        routers = super()._get_fastapi_routers()
        if self.app == 'api_sync_order':
            fapi = FastAPI()
            fapi.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],  # Cho phép tất cả các nguồn
                allow_credentials=True,
                allow_methods=["*"],  # Cho phép tất cả các phương thức
                allow_headers=["*"],  # Cho phép tất cả các headers
            )
            from ..routers import sync_order
            routers.extend([sync_order.router])
            fapi.include_router(sync_order.router)
        return routers
