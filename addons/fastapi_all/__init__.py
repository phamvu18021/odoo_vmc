from . import models
from . import routers
from . import schemas

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# # Khởi tạo ứng dụng FastAPI
# app = FastAPI()
#
# # Cấu hình CORS middleware cho FastAPI
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Cấu hình origin phù hợp
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# app.include_router(routers.admissions.router)
