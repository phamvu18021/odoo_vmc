from typing import List, Optional

from pydantic import BaseModel, field_validator


class ShortCourseWordPressRequest(BaseModel):
    idWordPress: str
    idOdoo: str
    slug: str


class ListShortCourseRequest(BaseModel):
    fields: str = "all"
    owner: str = "all"
    perpage: int = 99
    page: int = 1


class OwnerShortCourse(BaseModel):
    name: str
    code: str


class TeachFieldShortCourse(BaseModel):
    name: str
    code: str


class CourseTeacher(BaseModel):
    id: int
    name: str
    image: Optional[str] = None
    name_to_slug: Optional[str] = None
    description: Optional[str] = None

    @field_validator("image", "description", "name_to_slug",
                     mode="before")
    def convert_false_to_none(cls, value):
        return value if value is not False else None


class SubCategory(BaseModel):
    id: int
    name: str
    slug: str


class GetCourseBySlugData(BaseModel):
    id: int
    name: str
    image: Optional[str] = None
    price: float
    teacher: Optional[CourseTeacher] = None
    time: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    slug_url: Optional[str] = None
    category: Optional[str] = None
    category_slug: Optional[str] = None

    @field_validator("description", "image", "time", "duration", "description",
                     "category", "slug_url", "teacher", "category_slug",
                     mode="before")
    def convert_false_to_none(cls, value):
        return value if value is not False else None


class ListShortCourseData(BaseModel):
    short_course: List[GetCourseBySlugData]
    is_last_page: bool
    total_documents: int


class ListShortCourseResponse(BaseModel):
    status: str
    message: str
    data: ListShortCourseData


class ListTeachersResponse(BaseModel):
    status: str
    message: str
    data: List[CourseTeacher]


class SubCategory(BaseModel):
    id: int
    name: str
    slug: Optional[str] = None

    @field_validator("slug",
                     mode="before")
    def convert_false_to_none(cls, value):
        return value if value is not False else None


class CategoryData(BaseModel):
    id: int
    name: str
    slug: Optional[str] = None
    child_categories: List["CategoryData"]  # Danh sách danh mục con (đệ quy)

    @field_validator("slug",
                     mode="before")
    def convert_false_to_none(cls, value):
        return value if value is not False else None


class ProductCategoriesResponse(BaseModel):
    success: bool
    data: Optional[List[CategoryData]] = None
    error: Optional[str] = None


class ProductCategoryRequest(BaseModel):
    type: str  # "all" hoặc "consensus"


class OrderLine(BaseModel):
    product_id: int
    product_uom_qty: int


class UserCreate(BaseModel):
    name: str
    email: str
    phone: str


class CreateSaleOrderRequest(BaseModel):
    partner_id: Optional[int] = None
    order_lines: List[OrderLine] = []
    voucher_code: Optional[str] = None
    user: Optional[UserCreate] = None


class CreateSaleOrderResponse(BaseModel):
    success: Optional[bool] = None
    name: Optional[str] = None
    error: Optional[str] = None


class GetCourseBySlugRequest(BaseModel):
    slug: str


class CheckDiscountRequest(BaseModel):
    discount_code: str


class GetCourseBySlugResponse(BaseModel):
    data: GetCourseBySlugData
    message: str


class DiscountDetail(BaseModel):
    discount: float
    discount_product_id: int
    description: str


class CheckDiscountResponse(BaseModel):
    success: Optional[bool] = None
    discount: Optional[DiscountDetail] = None
    error: Optional[str] = None


class OrderLineGet(BaseModel):
    product_name: str
    description: str
    quantity: float
    unit_price: float
    total_price: float


class OrderData(BaseModel):
    order_id: int
    name: str
    amount_total: float
    date_order: str
    state: str
    order_lines: List[OrderLineGet]


class PartnerOrdersRequest(BaseModel):
    partner_id: int


class PartnerOrdersResponse(BaseModel):
    success: Optional[bool] = None
    orders: Optional[List[OrderData]] = None
    error: Optional[str] = None


class UserAccessRequest(BaseModel):
    partner_id: Optional[int] = None


class UserAccessResponse(BaseModel):
    status: str
    message: str
    access_count: Optional[int] = None


class StatsData(BaseModel):
    totalVisits: int
    totalSellers: int
    newSellers: int
    totalProducts: int
    newProducts: int
    totalOrders: int
    successfulOrders: int
    failedOrders: int
    totalTransactionValue: float


class StatsResponse(BaseModel):
    data: Optional[StatsData] = None
    message: Optional[str] = None
    error: Optional[str] = None
