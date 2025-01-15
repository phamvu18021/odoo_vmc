from odoo import models, api, fields
import datetime


class ThWizardImport(models.TransientModel):

    _name = 'report.export_xlsx'
    _description = 'export data sql'
    _inherit = 'report.report_xlsx.abstract'

    th_model_id = fields.Many2one('ir.model')
    th_data_export = fields.Boolean('Có xuất dữ liệu', default=False)
    th_type = fields.Selection(selection=[('create', 'Tạo'), ('update', 'Cập nhập')])

    def generate_xlsx_report(self, workbook, data, table):
        worksheet = workbook.add_worksheet('Export data template')
        table_name = table.th_model_id.model.replace('.', '_')
        query = ''' SELECT * FROM %s''' % table_name
        self.env.cr.execute(query)
        key_header = []

        if table.th_data_export:
            result = self.env.cr.dictfetchall()
            for rec in result:
                for key in rec.keys():
                    key_header.append({
                        'header': key,
                        'type': self.env[f'{table.th_model_id.model}']._fields[key].type
                    })
                break
            self.env.cr.execute(query)
            datas = self.env.cr.fetchall()
        else:
            result = self.env.cr.dictfetchone()
            for rec in result.keys():
                key_header.append({
                    'header': rec,
                    'type': self.env[f'{table.th_model_id.model}']._fields[rec].type
                })

            self.env.cr.execute(query)
            datas = self.env.cr.fetchone()

        self.generate_header(workbook, data, table, worksheet, key_header)
        self.generate_content(workbook, data, table, worksheet, datas)

    def generate_header(self, workbook, data, table, worksheet, key_header):
        header_format = workbook.add_format(
            {'bold': True, 'font_name': 'Times New Roman', 'font_size': 11, 'align': 'center',
             'valign': 'vcenter',
             'text_wrap': True, 'border': 1})
        title_format = workbook.add_format(
            {'bold': True, 'font_name': 'Times New Roman', 'font_size': 12, 'align': 'center',
             'valign': 'vcenter',
             'text_wrap': True})
        # Generate Header
        col = 0
        for value in key_header:
            worksheet.write(0, col, value['header'], header_format)
            worksheet.write(1, col, value['type'], header_format)
            col += 1

    def generate_content(self, workbook, data, partners, worksheet, datas):
        date_format = workbook.add_format(
            {'font_name': 'Times New Roman', 'font_size': 11, 'num_format': 'dd/mm/yyyy', 'right': 1, 'bottom': 3})

        datetime_format = workbook.add_format(
            {'font_name': 'Times New Roman', 'font_size': 11, 'num_format': 'dd/mm/yyyy h:mm', 'right': 1, 'bottom': 3})
        normal_format = workbook.add_format(
            {'font_name': 'Times New Roman', 'font_size': 11, 'num_format': '@', 'right': 1, 'bottom': 3})
        number_format = workbook.add_format(
            {'font_name': 'Times New Roman', 'font_size': 11,
             'num_format': '_(* #,##0.0_);_(* (#,##0.0);_(* "-"??_);_(@_)', 'right': 1, 'bottom': 1})

        # Generate data
        start_row_index = 2
        col = 0
        for data in datas:
            if type(datas) == tuple:
                if type(data) == datetime.datetime or type(data) == datetime.date:
                    worksheet.write(start_row_index, col, data, date_format if type(data) == datetime.date else datetime_format)
                else:
                    worksheet.write(start_row_index, col, data, normal_format)
                col += 1
            else:
                col = 0
                for value in data:

                    if type(value) == datetime.datetime or type(value) == datetime.date:
                        worksheet.write(start_row_index, col, value, date_format if type(data) == datetime.date else datetime_format)
                    else:
                        worksheet.write(start_row_index, col, value, normal_format)
                    col += 1
                start_row_index += 1

    def action_export_data(self):
        return self.env.ref('th_base.th_data_report_xlsx').report_action(self)
