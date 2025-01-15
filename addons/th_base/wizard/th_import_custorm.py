import base64
import datetime
import json
import xlrd

from odoo import models, api, fields
from psycopg2.extras import Json

from odoo.exceptions import ValidationError
from itertools import zip_longest

key_format = '"{}"'.format
value_format = "'{}'".format


class ThWizardImport(models.TransientModel):
    _name = 'th.import.cus'
    _description = 'import all sql'

    file = fields.Binary('File', help="File to check and/or import, raw binary (not base64)", attachment=False)
    th_model_id = fields.Many2one('ir.model')

    def action_import_data(self):
        try:
            self.action_import()
        except Exception as e:
            raise ValidationError(e)

        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'reload',
        # }

    def action_import(self):
        wb = xlrd.open_workbook(file_contents=base64.decodebytes(self.file))
        sheet = wb.sheet_by_index(0)
        start_row = 2
        table_name = self.th_model_id.model.replace('.', '_')
        for i in range(start_row, sheet.nrows):
            header = sheet.row_values(0)
            th_type = sheet.row_values(1)
            rows = sheet.row_values(i)
            th_id = rows[0]
            del header[0]
            del rows[0]
            del th_type[0]
            try:
                for index in [i for i, n in enumerate(th_type) if n == 'datetime']:
                    rows[index] = xlrd.xldate.xldate_as_datetime(float(rows[index]), 0)

                for index in [i for i, n in enumerate(th_type) if n == 'date']:
                    rows[index] = xlrd.xldate.xldate_as_datetime(float(rows[index]), 0).date()

                for index in [i for i, n in enumerate(th_type) if n in ['many2one', 'integer']]:
                    rows[index] = int(rows[index])

                for index in [i for i, n in enumerate(th_type) if n in ['one2many', 'many2many']]:
                    if rows[index] and type(rows[index]) == str:
                        rows[index] = [[6, 0, rows[index].split(',')]]
                    else:
                        rows[index] = [[6, 0, [int(rows[index])]]]

                for index in [i for i, n in enumerate(th_type) if n in ['boolean']]:
                    if rows[index]:
                        rows[index] = True if rows[index] in ['1', 'True', 1] else False

                # Sử dụng zip_longest để kết hợp các phần tử của hai danh sách thành các cặp
                zipped_lists = zip_longest(header, rows, fillvalue=None)
                # Chuyển các cặp này thành một dictionary
                result_dict = dict(zipped_lists)
                # Loại bỏ các phần tử có giá trị rỗng hoặc None
                cleaned_dict = {key: value for key, value in result_dict.items() if value not in [None, '']}

                if not th_id:
                    self.env[self.th_model_id.model].create(cleaned_dict)
                else:
                    self.env[self.th_model_id.model].browse(int(th_id)).write(cleaned_dict)

            except Exception as e:
                raise ValidationError(f'Lỗi ở dòng số:{i}, Mã lỗi: ' + str(e))
