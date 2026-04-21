import io
import base64
import xlsxwriter

from odoo import models, fields
from odoo.exceptions import UserError


class BookReport(models.Model):
    _name = 'book.report'
    _description = 'Book Report'

    name = fields.Char()
    author = fields.Char()
    price = fields.Float()

    def action_export_excel(self):
        if not self:
            raise UserError('No records to export.')

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Books')

        # Header
        sheet.write(0, 0, 'Name')
        sheet.write(0, 1, 'Author')
        sheet.write(0, 2, 'Price')

        records = self

        row = 1
        for rec in records:
            sheet.write(row, 0, rec.name or '')
            sheet.write(row, 1, rec.author or '')
            sheet.write(row, 2, rec.price or 0)
            row += 1

        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())

        return {
            'type': 'ir.actions.act_url',
            'url': 'data:application/vnd.ms-excel;base64,' + file_data.decode(),
            'target': 'self',
        }