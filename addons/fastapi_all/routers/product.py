import os
from typing import Annotated, List

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Response

from odoo.addons.test_convert.tests.test_env import record
from odoo.api import Environment
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from ..schemas.product import ShortCourseWordPressRequest, ListShortCourseResponse, ListShortCourseData, \
    OrderLine, CreateSaleOrderResponse, UserCreate, GetCourseBySlugResponse, \
    CourseTeacher, CheckDiscountResponse, DiscountDetail, OrderData, PartnerOrdersResponse, UserAccessResponse, \
    StatsResponse, OrderLineGet, StatsData, CheckDiscountRequest, \
    PartnerOrdersRequest, UserAccessRequest, GetCourseBySlugData, CreateSaleOrderRequest, ProductCategoriesResponse, \
    SubCategory, CategoryData, ListTeachersResponse, ProductCategoryRequest
from ...fastapi.dependencies import odoo_env

router = APIRouter()

load_dotenv()
ODOO_SECRET = os.getenv('TOKEN')

auth_scheme = HTTPBearer()


@router.options("/shortcourse-wordpress")
async def options_shortcourse_wordpress():
    headers = {
        "Access-Control-Allow-Origin": "*",  # Cho phép tất cả các nguồn
        "Access-Control-Allow-Methods": "POST, OPTIONS",  # Cho phép POST và OPTIONS
        "Access-Control-Allow-Headers": "Content-Type, Authorization",  # Cho phép các header cần thiết
    }
    return Response(status_code=200, headers=headers)


@router.post("/shortcourse-wordpress")
async def admission_wordpress(
        request: ShortCourseWordPressRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")

    try:
        th_short_course = env['product.template'].sudo().search([('id', '=', request.idOdoo)])
        if th_short_course.exists():
            vals = {
                'idWordPress': request.idWordPress,
                'slug_url': request.slug
            }
            th_short_course.sudo().write(vals)
            return {"Message": "Success", "status_code": 201}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("/product-categories", response_model=ProductCategoriesResponse)
# async def get_product_categories(
#         env: Environment = Depends(odoo_env),
#         credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
# ):
#     token = credentials.credentials
#     if token != ODOO_SECRET:
#         raise HTTPException(status_code=403, detail="Invalid secret code")
#
#     try:
#         categories = env['product.category'].sudo().search([('product_count', '>', 0)])
#         categories_data = []
#
#         for category in categories:
#             parent_category = None
#             if category.parent_id:
#                 parent_category = SubCategory(id=category.parent_id.id, name=category.parent_id.name,
#                                               slug=category.parent_id.slug)
#
#             child_categories = [
#                 SubCategory(id=child.id, name=child.name, slug=child.slug)
#                 for child in category.child_id
#             ]
#
#             categories_data.append(
#                 CategoryData(
#                     id=category.id,
#                     name=category.name,
#                     slug=category.slug,
#                     parent_category=parent_category,
#                     child_categories=child_categories
#                 )
#             )
#
#         return ProductCategoriesResponse(success=True, data=categories_data)
#     except Exception as e:
#         return ProductCategoriesResponse(success=False, error=str(e))

@router.post("/product-categories", response_model=ProductCategoriesResponse)
async def get_product_categories(
        request: ProductCategoryRequest,
        env: Environment = Depends(odoo_env),
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")

    try:
        # Chỉ lấy danh mục được tích "Hiển thị trên website"
        categories = env['product.category'].sudo().search_read(
            [('is_show_on_website', '!=', True)],
            ['id', 'name', 'slug', 'parent_id', 'sequence'],
            order='sequence ASC'
        )

        # Tạo dictionary để tra cứu nhanh
        category_map = {cat['id']: cat for cat in categories}

        # Nếu type = "all", trả về danh sách phẳng
        if request.type == "all":
            return ProductCategoriesResponse(
                success=True,
                data=[
                    CategoryData(
                        id=cat['id'],
                        name=cat['name'],
                        slug=cat['slug'],
                        child_categories=[]
                    ) for cat in categories
                ]
            )

        # Nếu type = "consensus", xây dựng cây danh mục
        def build_category_tree(category_id):
            category = category_map.get(category_id)
            if not category:
                return None

            child_categories = [
                build_category_tree(child_id)
                for child_id in category_map
                if category_map[child_id].get('parent_id') and category_map[child_id]['parent_id'][0] == category_id
            ]
            child_categories = [c for c in child_categories if c]

            return CategoryData(
                id=category['id'],
                name=category['name'],
                slug=category['slug'],
                child_categories=child_categories
            )

        # Chỉ lấy danh mục gốc (không có parent_id)
        root_categories = [
            build_category_tree(cat['id'])
            for cat in categories if not cat.get('parent_id')
        ]

        return ProductCategoriesResponse(success=True, data=root_categories)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("/list-shortcourse", response_model=ListShortCourseResponse)
# async def list_short_course(
#         env: Annotated[Environment, Depends(odoo_env)],
#         categories: Optional[str] = None,  # Danh sách slug của danh mục, ví dụ: "nghe-thuat,cong-nghe"
#         teacher: Optional[str] = None,
#         perpage: int = 9,
#         page: int = 1,
#         credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
# ):
#     token = credentials.credentials
#     if token != ODOO_SECRET:
#         raise HTTPException(status_code=403, detail="Invalid secret code")
#
#     try:
#         # Xây dựng domain lọc
#         domain = [('purchase_ok', '=', True)]
#         if categories != "all":
#             # Tách các slug từ categories
#             category_slugs = categories.split(',')
#
#             # Lấy các danh mục từ slug
#             list_categories = env['product.category'].sudo().search([('slug', 'in', category_slugs)])
#             all_category_ids = set(list_categories.ids)
#
#             # Lấy danh mục con (nếu có)
#             for category in list_categories:
#                 child_categories = category.child_id
#                 all_category_ids.update(child_categories.ids)
#
#             domain.append(('categ_id', 'in', list(all_category_ids)))
#
#         if teacher != 'all':
#             domain.append(('th_teacher_id.name_to_slug', '=', teacher))
#
#         # Tính toán phân trang
#         offset = (page - 1) * perpage if perpage > 0 else 0
#         records = env['product.template'].sudo().search(domain, offset=offset, limit=perpage)
#
#         # Xử lý dữ liệu trả về
#         data = [
#             GetCourseBySlugData(
#                 id=record.id,
#                 name=record.with_context({'lang': 'vi_VN'}).name,
#                 image=record.image_shortcourse_url or "",
#                 category=str(record.categ_id.name) if record.categ_id else None,
#                 category_slug=record.categ_id.slug,
#                 teacher=CourseTeacher(
#                     id=record.th_teacher_id.id,
#                     name=record.th_teacher_id.name,
#                     image=record.th_teacher_id.th_img_banner_url,
#                     name_to_slug=record.th_teacher_id.name_to_slug,
#                     description=record.th_teacher_id.description
#                 ),
#                 price=record.list_price,
#                 duration=record.duration,
#                 time=record.time,
#                 desc=record.description,
#                 slug_url=record.slug_url
#             )
#             for record in records
#         ]
#
#         total_documents = len(env['product.template'].sudo().search(domain))
#         is_last_page = (offset + perpage) >= total_documents
#
#         return ListShortCourseResponse(
#             status="200",
#             message="Successfully fetched short courses",
#             data=ListShortCourseData(short_course=data, is_last_page=is_last_page, total_documents=total_documents)
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/list-shortcourse", response_model=ListShortCourseResponse)
async def list_short_course(
        env: Annotated[Environment, Depends(odoo_env)],
        categories: Optional[str] = None,
        teacher: Optional[str] = None,
        perpage: int = 9,
        page: int = 1,
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")

    try:
        domain = [('purchase_ok', '=', True)]

        # Xử lý danh mục
        if categories != "all":
            category_slugs = categories.split(',')

            # Tìm danh mục cha theo slug
            list_categories = env['product.category'].sudo().search([('slug', 'in', category_slugs)])

            if list_categories:
                # Lấy tất cả danh mục con của danh mục cha, bao gồm nhiều cấp độ
                all_category_ids = env['product.category'].sudo().search([('id', 'child_of', list_categories.ids)]).ids
                domain.append(('categ_id', 'in', all_category_ids))

        # Xử lý giáo viên
        if teacher and teacher != 'all':
            domain.append(('th_teacher_id.name_to_slug', '=', teacher))

        # Phân trang
        offset = (page - 1) * perpage
        records = env['product.template'].sudo().search(domain, offset=offset, limit=perpage)

        # Xử lý dữ liệu
        data = []
        for record in records:
            teacher_data = None
            if record.th_teacher_id:
                teacher_data = CourseTeacher(
                    id=record.th_teacher_id.id,
                    name=record.th_teacher_id.name,
                    image=record.th_teacher_id.th_img_banner_url,
                    name_to_slug=record.th_teacher_id.name_to_slug,
                    description=record.th_teacher_id.description
                )

            data.append(GetCourseBySlugData(
                id=record.id,
                name=record.with_context({'lang': 'vi_VN'}).name,
                image=record.image_shortcourse_url or "",
                category=record.categ_id.name if record.categ_id else None,
                category_slug=record.categ_id.slug if record.categ_id else None,
                teacher=teacher_data,
                price=record.list_price,
                price_promo=record.price_promo if record.price_promo else None,
                duration=record.duration,
                time=record.time,
                number_of_lessons=record.number_of_lessons,
                number_of_student=record.number_of_student,
                desc=record.description,
                slug_url=record.slug_url
            ))

        total_documents = env['product.template'].sudo().search_count(domain)
        is_last_page = (offset + perpage) >= total_documents

        return ListShortCourseResponse(
            status="200",
            message="Successfully fetched short courses",
            data=ListShortCourseData(
                short_course=data,
                is_last_page=is_last_page,
                total_documents=total_documents
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post("/get_course_by_slug", response_model=GetCourseBySlugResponse)
async def get_course_by_slug(
        slug: str,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")

    try:
        records = env['product.template'].sudo().search([('slug_url', '=', slug)], limit=1)
        if not records:
            raise HTTPException(status_code=404, detail=f"Course with slug '{slug}' not found")
        course = records[0]
        return GetCourseBySlugResponse(
            data=GetCourseBySlugData(
                id=course.id,
                name=course.with_context({'lang': 'vi_VN'}).name,
                price_promo=course.price_promo if course.price_promo else None,
                image=course.image_shortcourse_url,
                category=str(course.categ_id.name) if course.categ_id else None,
                price=course.list_price,
                teacher=CourseTeacher(
                    id=course.th_teacher_id.id,
                    name=course.th_teacher_id.name,
                    image=course.th_teacher_id.th_img_banner_url,
                    name_to_slug=course.th_teacher_id.name_to_slug,
                    description=course.th_teacher_id.description
                ),
                time=course.time,
                number_of_lessons=course.number_of_lessons,
                number_of_student=course.number_of_student,
                category_slug=course.categ_id.slug,
                duration=course.duration,
                description=course.description,
                slug_url=course.slug_url
            ),
            message="success"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/list-teachers", response_model=ListTeachersResponse)
async def list_teachers(
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")

    try:
        # Lấy danh sách giáo viên từ Odoo
        teachers = env['th.teacher'].sudo().search([])

        # Xử lý dữ liệu trả về
        teacher_data = [
            CourseTeacher(
                id=teacher.id,
                name=teacher.name,
                image=teacher.th_img_banner_url,
                name_to_slug=teacher.name_to_slug,
                description=teacher.description
            )
            for teacher in teachers
        ]
        return ListTeachersResponse(
            data=teacher_data,
            message="success",
            status="200"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_sale_order", response_model=CreateSaleOrderResponse)
async def create_sale_order(
        env: Annotated[Environment, Depends(odoo_env)],
        request: CreateSaleOrderRequest,
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")
    try:
        partner_id = request.partner_id
        if not partner_id:
            user_info = request.user or {}
            existing_partner = env['res.partner'].sudo().search([('email', '=', user_info.email)], limit=1)
            if existing_partner:
                existing_partner.sudo().write({'name': user_info.name, 'phone': user_info.phone})
                partner_id = existing_partner.id
            else:
                partner = env['res.partner'].sudo().create({
                    'name': user_info.name,
                    'phone': user_info.phone,
                    'email': user_info.email,
                })
                partner_id = partner.id
        processed_order_lines = []
        for line in request.order_lines:
            product = env['product.template'].sudo().browse(line.product_id)
            if not product.exists():
                return {"error": f"Product with id {line.product_id} does not exist"}
            processed_order_lines.append((0, 0, {
                'product_id': line.product_id,
                'product_uom_qty': line.product_uom_qty,
                'price_unit': product.list_price
            }))

        sale_order = env['sale.order'].sudo().create({
            'partner_id': partner_id,
            'order_line': processed_order_lines,
        })
        sale_order.action_confirm()

        if request.voucher_code:
            loyalty_program = env['loyalty.program'].sudo().search([('rule_ids.code', '=', request.voucher_code)],
                                                                   limit=1)
            if not loyalty_program:
                return CreateSaleOrderResponse(success=False, error="Invalid voucher code")

            reward = loyalty_program.reward_ids[0]
            discount_percentage = reward.discount
            discount_product_id = reward.discount_line_product_id.id
            discounted_amount = sum(
                line.price_unit * line.product_uom_qty * discount_percentage / 100 for line in sale_order.order_line)

            env['sale.order.line'].sudo().create({
                'order_id': sale_order.id,
                'product_id': discount_product_id,
                'name': request.voucher_code,
                'price_unit': -discounted_amount,
                'product_uom_qty': 1
            })

        return CreateSaleOrderResponse(success=True, name=sale_order.name)

    except Exception as e:
        return CreateSaleOrderResponse(success=False, error=str(e))


@router.post("/check_discount", response_model=CheckDiscountResponse)
async def check_discount(
        request: CheckDiscountRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")
    try:
        voucher_code = request.discount_code

        loyalty_program = env['loyalty.program'].sudo().search([
            ('rule_ids.code', '=', voucher_code)
        ], limit=1)
        if not loyalty_program:
            return CheckDiscountResponse(error="Invalid voucher code")

        reward = loyalty_program.reward_ids[0]
        discount = DiscountDetail(
            discount=reward.discount,
            discount_product_id=reward.discount_line_product_id.id,
            description=reward.description
        )
        return CheckDiscountResponse(success=True, discount=discount)
    except Exception as e:
        return CheckDiscountResponse(error=str(e))


@router.post("/get_partner_orders", response_model=PartnerOrdersResponse)
async def get_partner_orders(
        request: PartnerOrdersRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)

):
    token = credentials.credentials
    if token != ODOO_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret code")
    try:
        partner_id = request.partner_id
        sale_orders = env['sale.order'].sudo().search([('partner_id', '=', partner_id)])

        orders_data = []
        for order in sale_orders:
            order_lines_data = [
                OrderLineGet(
                    product_name="Mã giảm giá" if line.price_unit < 0 else line.product_id.name,
                    description=line.name,
                    quantity=line.product_uom_qty,
                    unit_price=line.price_unit,
                    total_price=line.price_subtotal
                )
                for line in order.order_line
            ]
            orders_data.append(
                OrderData(
                    order_id=order.id,
                    name=order.name,
                    amount_total=order.amount_total,
                    date_order=str(order.date_order),
                    state=order.state,
                    order_lines=order_lines_data
                )
            )
        return PartnerOrdersResponse(success=True, orders=orders_data)
    except Exception as e:
        return PartnerOrdersResponse(error=str(e))


@router.post("/user_access", response_model=UserAccessResponse)
async def user_access(
        request: UserAccessRequest,
        env: Annotated[Environment, Depends(odoo_env)],
        credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),

):
    try:
        token = credentials.credentials
        if token != ODOO_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret code")
        partner_id = request.partner_id

        if partner_id:
            user_access_record = env['user.access'].search([('partner', '=', partner_id)], limit=1)
            if user_access_record:
                user_access_record.access_count += 1
                return UserAccessResponse(status="success", message="Access count updated.",
                                          access_count=user_access_record.access_count)
            else:
                new_access_record = env['user.access'].create({
                    'name': f'Access record for partner {partner_id}',
                    'partner': partner_id,
                    'access_count': 1
                })
                return UserAccessResponse(status="success", message="New access record created.",
                                          access_count=new_access_record.access_count)
        else:
            user_access_record = env['user.access'].search([('partner', '=', False)], limit=1)
            if user_access_record:
                user_access_record.access_count += 1
                return UserAccessResponse(status="success", message="Access count updated for unpartnered record.",
                                          access_count=user_access_record.access_count)
            else:
                return UserAccessResponse(status="error", message="No unpartnered access record found.")
    except Exception as e:
        return UserAccessResponse(status="error", message=str(e))
