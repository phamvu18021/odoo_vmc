import base64
import datetime
import json
import xlrd

from odoo import models, api, fields
from psycopg2.extras import Json

from odoo.exceptions import ValidationError

key_format = '"{}"'.format
value_format = "'{}'".format


class ThWizardImport(models.TransientModel):
    _name = 'th.import'
    _description = 'import all sql'

    file = fields.Binary('File', help="File to check and/or import, raw binary (not base64)", attachment=False)
    th_model_id = fields.Many2one('ir.model')
    th_type = fields.Selection(selection=[('create', 'Tạo'), ('update', 'Cập nhập')])
    th_is_active = fields.Boolean(string='Bảng có trường Active', default=True)

    def action_import_data(self):
        try:
            self.action_import()
        except Exception as e:
            raise ValidationError(e)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_import(self):
        wb = xlrd.open_workbook(file_contents=base64.decodebytes(self.file))
        sheet = wb.sheet_by_index(0)
        start_row = 2
        table_name = self.th_model_id.model.replace('.', '_')
        for i in range(start_row, sheet.nrows):
            header = sheet.row_values(0)
            th_type = sheet.row_values(1)
            rows = sheet.row_values(i)
            if 'active' not in header and self.th_is_active:
                header.append("active")
                th_type.append("boolean")
                rows.append(1)

            if self.th_type == 'create':
                del header[0]
                del rows[0]
                del th_type[0]
                cols = ", ".join(key_format(fname) for fname in header)
                # values = ', '.join(value_format(row) if row else "NULL" if type(row) == str else f'{row}' for row in rows)
                values = ''
                for index in range(0, len(header)):
                    if header[index] == 'id':
                        continue

                    if rows[index]:
                        if index != 0:
                            if th_type[index] in ["boolean"]:
                                values += ', true' if rows[index] == 1 else ', false'
                            elif th_type[index] in ["boolean"] and header[index] == 'active':
                                values += ', true'
                            elif th_type[index] == "datetime" and rows[index]:
                                try:
                                    values += f", '{xlrd.xldate.xldate_as_datetime(float(rows[index]), 0)}'"
                                except ValueError:
                                    values += f", '{rows[index]}'"

                            elif th_type[index] == "date" and rows[index]:
                                try:
                                    values += f", '{xlrd.xldate.xldate_as_datetime(float(rows[index]), 0).date()}'"
                                except ValueError:
                                    values += f", '{rows[index]}'"
                            else:
                                values += f", '{rows[index]}'" if type(rows[index]) == str else f", {rows[index]}"
                        else:
                            if th_type[index] in ["boolean"]:
                                values += ' true' if rows[index] == 1 else ' false'
                            elif th_type[index] in ["boolean"] and header[index] == 'active':
                                values += ' true'
                            elif th_type[index] == "datetime" and rows[index]:
                                try:
                                    values += f"'{xlrd.xldate.xldate_as_datetime(float(rows[index]), 0)}'"
                                except ValueError:
                                    values += f", '{rows[index]}'"

                            elif th_type[index] == "date" and rows[index]:
                                try:
                                    values += f"'{xlrd.xldate.xldate_as_datetime(float(rows[index]), 0).date()}'"
                                except ValueError:
                                    values += f"'{rows[index]}'"
                            else:
                                values += f"'{rows[index]}'" if type(rows[index]) == str else f"{rows[index]}"
                    else:
                        if th_type[index] == "datetime" and header[index] == 'create_date':
                            values += f"'{datetime.datetime.now()}'" if index == 0 else f", '{datetime.datetime.now()}'"
                        else:
                            values += ' NUll' if index == 0 else ', NUll'

                query = f'insert into {table_name} ({cols}) VALUES ({values})'
                self.env.cr.execute(query)
            else:
                query = f'UPDATE {table_name} SET '
                for index in range(0, len(header)):
                    data_import = "NULL"
                    if header[index] == 'id':
                        continue

                    if rows[index]:
                        data_import = f"'{rows[index]}'"

                    if type(rows[index]) in [int, float]:
                        data_import = f"{rows[index]}"

                    if th_type[index] == "datetime" and rows[index]:
                        try:
                            data_import = f"'{xlrd.xldate.xldate_as_datetime(float(rows[index]), 0)}'"
                        except ValueError:
                            pass

                    if th_type[index] == "date" and rows[index]:
                        try:
                            data_import = f"'{xlrd.xldate.xldate_as_datetime(float(rows[index]), 0)}'"
                        except ValueError:
                            pass

                    if th_type[index] in ["boolean"]:
                        data_import = 'true' if rows[index] == 1 else 'false'

                    query += f'{header[index]} = {data_import} ' if index == len(header) - 1 else f'{header[index]} = {data_import}, '

                self.env.cr.execute(query + f'where id = {int(rows[0])}')
