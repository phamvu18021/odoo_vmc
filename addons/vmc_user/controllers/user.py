from odoo import http, api
from odoo.http import request, Response
import json

headers = {
    'Content-Type': 'application/json',
}


class UserController(http.Controller):
    @http.route('/api/register', type='json', auth="none", cors='*', methods=['POST'], csrf=False)
    def register(self):
        try:
            client_headers = request.httprequest.headers
            client_values = request.httprequest.data
            body_str = client_values.decode('utf-8')
            data = json.loads(body_str)
            # Lấy dữ liệu từ body của request (JSON)

            # Kiểm tra các trường trong body
            email = data.get('email')
            name = data.get('name')
            password = data.get('password')

            if not email or not name or not password:
                return {"error": "Thiếu thông tin cần thiết"}

            # Kiểm tra xem email đã tồn tại trong hệ thống hay chưa
            existing_partner = request.env['res.partner'].sudo().search([('email', '=', email)])
            if existing_partner:
                return {"error": "Email đã tồn tại"}

            new_partner = request.env['res.partner'].sudo().create({
                'name': name,
                'email': email,
                'password': password,
                'phone': 0,
                'status': False  # status ban đầu là False
            })

            return {"success": "Tạo tài khoản thành công", "partner_id": new_partner.id}
        except Exception as e:
            response_data = {"error": str(e)}
            return Response(json.dumps(response_data), status=500)

    @http.route('/api/activate_account', type='json', auth="none", cors='*', methods=['POST'], csrf=False)
    def activate_account(self):
        try:
            # Lấy dữ liệu từ body của request (JSON)
            client_values = request.httprequest.data
            body_str = client_values.decode('utf-8')
            data = json.loads(body_str)

            email = data.get('email')
            password = data.get('password')

            # Kiểm tra nếu email hoặc mật khẩu không có trong body
            if not email or not password:
                return {"error": "Thiếu thông tin email hoặc mật khẩu"}

            # Tìm kiếm record trong res.partner với email và mật khẩu
            partner = request.env['res.partner'].sudo().search([
                ('email', '=', email),
                ('password', '=', password),  # Nên lưu mật khẩu đã được mã hóa
                ('status', '=', False)  # Kiểm tra trạng thái tài khoản chưa được kích hoạt
            ], limit=1)

            if partner:
                # Cập nhật trạng thái thành đã kích hoạt (True)
                partner.sudo().write({'status': True})
                return {"success": "Kích hoạt tài khoản thành công", "partner_id": partner.id}
            else:
                return {"error": "Email hoặc mật khẩu không chính xác, hoặc tài khoản đã được kích hoạt"}

        except Exception as e:
            response_data = {"error": str(e)}
            return Response(json.dumps(response_data), status=500)

    @http.route('/api/login', type='json', auth="none", cors='*', methods=['POST'], csrf=False)
    def login(self):
        try:
            # Lấy dữ liệu từ body của request (JSON)
            client_values = request.httprequest.data
            body_str = client_values.decode('utf-8')
            data = json.loads(body_str)

            # Lấy thông tin email và mật khẩu từ request body
            email = data.get('email')
            password = data.get('password')

            # Kiểm tra email và mật khẩu
            if not email or not password:
                return {"error": "Thiếu email hoặc mật khẩu"}

            # Tìm kiếm tài khoản với email và mật khẩu
            partner = request.env['res.partner'].sudo().search([
                ('email', '=', email),
                ('password', '=', password)
            ], limit=1)

            if not partner:
                # Sai tài khoản hoặc mật khẩu
                return {"error": "Sai tài khoản hoặc mật khẩu"}

            if partner.status == False:
                # Tài khoản chưa kích hoạt
                return {"error": "Tài khoản của bạn chưa được kích hoạt. Vui lòng kiểm tra email để kích hoạt."}
            # Trả về thông tin đăng nhập thành công và session ID
            return {
                "success": "Đăng nhập thành công",
                "partner_id": partner.id,
                "user": {
                    "email": partner.email,
                    "name": partner.name,
                    "phone": partner.phone,
                    "gender": partner.gender,
                    "age": partner.age
                }
            }

        except Exception as e:
            response_data = {"error": str(e)}
            return Response(json.dumps(response_data), status=500)

    @http.route('/api/get_user_info', type='json', auth="none", cors='*', methods=['POST'], csrf=False)
    def get_user_info(self):
        try:
            client_values = request.httprequest.data
            body_str = client_values.decode('utf-8')
            data = json.loads(body_str)

            partner_id = data.get('partner_id')

            if not partner_id:
                return {"error": "Thiếu thông tin partner_id"}

            partner = request.env['res.partner'].sudo().browse(partner_id)

            if not partner.exists():
                return {
                    "partner_id": partner_id,
                    "error": "Không tìm thấy tài khoản"}

            user_info = {
                'name': partner.name,
                'email': partner.email,
                'phone': partner.phone,
                'age': partner.age,
                'gender': partner.gender,
                'image': ""
                # Thêm các trường khác nếu cần
            }

            return {"success": "Lấy thông tin thành công", "user_info": user_info}

        except Exception as e:
            return {"error": str(e)}

    @http.route('/api/update_user_info', type='json', auth="none", cors='*', methods=['POST'], csrf=False)
    def update_user_info(self):
        try:
            # Lấy dữ liệu từ request
            client_values = request.httprequest.data
            body_str = client_values.decode('utf-8')
            data = json.loads(body_str)

            # Lấy partner_id và các dữ liệu cần cập nhật
            partner_id = data.get('partner_id')
            name = data.get('name')
            email = data.get('email')
            image = data.get('image')
            age = data.get('age')
            phone = data.get('phone')
            gender = data.get('gender')

            if not partner_id:
                return {"error": "Thiếu thông tin partner_id"}

            # Lấy đối tượng res.partner dựa trên partner_id
            partner = request.env['res.partner'].sudo().browse(partner_id)

            # Kiểm tra sự tồn tại của đối tượng
            if not partner.exists():
                return {"error": "Không tìm thấy tài khoản"}

            # Cập nhật thông tin đối tượng với các dữ liệu mới
            update_data = {}
            if name:
                update_data['name'] = name
            if email:
                update_data['email'] = email
            if age:
                update_data['age'] = age
            if phone:
                update_data['phone'] = phone
            if gender:
                update_data['gender'] = gender

            # Thực hiện cập nhật thông tin
            partner.sudo().write(update_data)
            return {"success": "Cập nhật thông tin thành công"}

        except Exception as e:
            # Xử lý lỗi và trả về thông báo lỗi
            return {"error": str(e)}

    @http.route('/api/change_password', type='json', auth="none", cors='*', methods=['POST'], csrf=False)
    def change_password(self):
        try:
            # Lấy dữ liệu từ request
            client_values = request.httprequest.data
            body_str = client_values.decode('utf-8')
            data = json.loads(body_str)

            # Lấy session_log_id, old_password và new_password
            session_log_id = data.get('session_log_id')
            old_password = data.get('old_password')
            new_password = data.get('new_password')

            if not session_log_id or not old_password or not new_password:
                return {"error": "Thiếu thông tin session_log_id, old_password hoặc new_password"}

            # Lấy đối tượng res.partner dựa trên session_log_id
            partner = request.env['res.partner'].sudo().browse(session_log_id)

            # Kiểm tra sự tồn tại của đối tượng
            if not partner.exists():
                return {"error": "Không tìm thấy tài khoản"}

            # Kiểm tra mật khẩu cũ
            if partner.password != old_password:
                return {"error": "Mật khẩu cũ không đúng"}

            # Cập nhật mật khẩu mới
            partner.sudo().write({'password': new_password})

            return {"success": "Đổi mật khẩu thành công"}

        except Exception as e:
            # Xử lý lỗi và trả về thông báo lỗi
            return {"error": str(e)}

    @http.route('/api/check_email', type='json', auth="none", cors='*', methods=['POST'], csrf=False)
    def check_email(self):
        try:
            # Lấy dữ liệu từ body của request (JSON)
            client_values = request.httprequest.data
            body_str = client_values.decode('utf-8')
            data = json.loads(body_str)

            # Lấy thông tin email từ request body
            email = data.get('email')

            # Kiểm tra email
            if not email:
                return {"error": "Thiếu email"}

            # Tìm kiếm partner với email
            partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)

            if not partner:
                # Không tìm thấy email trong hệ thống
                return {"exists": False, "message": "Email không tồn tại"}

            # Email tồn tại
            return {"exists": True, "message": "Email đã tồn tại"}

        except Exception as e:
            # Trả về lỗi nếu xảy ra ngoại lệ
            response_data = {"error": str(e)}
            return Response(json.dumps(response_data), status=500)

    @http.route('/api/reissue_password', type='json', auth="none", cors='*', methods=['POST'], csrf=False)
    def reissue_password(self):
        try:
            # Lấy dữ liệu từ body của request (JSON)
            client_values = request.httprequest.data
            body_str = client_values.decode('utf-8')
            data = json.loads(body_str)

            # Lấy thông tin email và mật khẩu mới
            email = data.get('email')
            new_password = data.get('new_password')

            # Kiểm tra email và mật khẩu
            if not email or not new_password:
                return {"error": "Thiếu email hoặc mật khẩu mới"}

            # Tìm kiếm tài khoản với email
            partner = request.env['res.partner'].sudo().search([
                ('email', '=', email)
            ], limit=1)

            if not partner:
                # Không tìm thấy tài khoản
                return {"error": "Email không tồn tại"}

            # Đặt lại mật khẩu mới
            partner.sudo().write({
                'password': new_password
            })

            # Trả về thông tin thành công
            return {
                "success": "Mật khẩu đã được cập nhật thành công",
                "partner_id": partner.id
            }

        except Exception as e:
            response_data = {"error": str(e)}
            return Response(json.dumps(response_data), status=500)

    @http.route('/api/cart/add-shortcourse', type='json', auth='none', methods=['POST'], csrf=False)
    def add_shortcourse(self):
        # Lấy dữ liệu từ body của request
        client_values = request.httprequest.data
        body_str = client_values.decode('utf-8')
        data = json.loads(body_str)

        # Lấy partner_id và shortcourse_id từ request body
        partner_id = data.get('partner_id')
        shortcourse_id = data.get('shortcourse_id')

        # Kiểm tra xem partner_id và shortcourse_id có hợp lệ không
        if not partner_id or not shortcourse_id:
            return {'error': 'Partner ID and ShortCourse ID are required.'}

        # Tìm đối tác
        partner = request.env['res.partner'].sudo().browse(partner_id)
        if not partner.exists():
            return {'error': 'Partner not found.'}

        # Tìm khóa học ngắn
        shortcourse = request.env['product.template'].sudo().browse(shortcourse_id)
        if not shortcourse.exists():
            return {'error': 'ShortCourse not found.'}

        # Kiểm tra xem khóa học ngắn đã tồn tại trong shortcourse_ids chưa
        shortcourse_rel = request.env['partner.shortcourse.rel'].sudo().search([
            ('partner_id', '=', partner_id),
            ('shortcourse_id', '=', shortcourse_id)
        ], limit=1)

        if shortcourse_rel:
            # Nếu đã tồn tại, tăng số lượng lên 1
            shortcourse_rel.quantity += 1
        else:
            # Nếu chưa tồn tại, tạo mới với số lượng mặc định là 1
            request.env['partner.shortcourse.rel'].sudo().create({
                'partner_id': partner_id,
                'shortcourse_id': shortcourse_id,
                'quantity': 1
            })

        return {'success': 'ShortCourse added to cart successfully.'}

    @http.route('/api/cart/subtract-shortcourse', type='json', auth='none', methods=['POST'], csrf=False)
    def subtract_shortcourse(self):
        # Lấy dữ liệu từ body của request
        client_values = request.httprequest.data
        body_str = client_values.decode('utf-8')
        data = json.loads(body_str)

        # Lấy partner_id, shortcourse_id và remove từ request body
        partner_id = data.get('partner_id')
        shortcourse_id = data.get('shortcourse_id')
        remove = data.get('remove', False)  # Mặc định là False

        # Kiểm tra xem partner_id và shortcourse_id có hợp lệ không
        if not partner_id or not shortcourse_id:
            return {'error': 'Partner ID and ShortCourse ID are required.'}

        # Tìm đối tác
        partner = request.env['res.partner'].sudo().browse(partner_id)
        if not partner.exists():
            return {'error': 'Partner not found.'}

        # Tìm khóa học ngắn
        shortcourse = request.env['product.template'].sudo().browse(shortcourse_id)
        if not shortcourse.exists():
            return {'error': 'ShortCourse not found.'}

        # Kiểm tra xem khóa học ngắn đã tồn tại trong shortcourse_ids chưa
        shortcourse_rel = request.env['partner.shortcourse.rel'].sudo().search([
            ('partner_id', '=', partner_id),
            ('shortcourse_id', '=', shortcourse_id)
        ], limit=1)

        if shortcourse_rel:
            if remove:
                # Nếu remove là True, xóa bản ghi mà không kiểm tra số lượng
                shortcourse_rel.unlink()
                return {'success': 'ShortCourse removed from cart successfully.'}
            else:
                # Nếu remove là False, giảm số lượng
                if shortcourse_rel.quantity > 1:
                    shortcourse_rel.quantity -= 1
                    return {'success': 'ShortCourse quantity decreased successfully.'}
                else:
                    # Nếu số lượng bằng 1, xóa bản ghi
                    shortcourse_rel.unlink()
                    return {'success': 'ShortCourse removed from cart successfully.'}
        else:
            return {'error': 'ShortCourse not found in cart.'}
