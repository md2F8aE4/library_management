from odoo import http
from odoo.http import request
import io
import xlsxwriter
from ast import literal_eval




class xlsxbookreport(http.Controller):

    @http.route('/library/book/excel/report/<string:book_ids>', type='http', auth='user')
    def download_xlsx_report(self, book_ids):
        try:
            parsed_ids = literal_eval(book_ids)
        except (ValueError, SyntaxError):
            parsed_ids = []

        books = request.env['library.book'].browse(parsed_ids)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Books Report')

        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 18)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 12)
        sheet.set_column('F:F', 18)

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center'
        })

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#444',
            'color': 'white',
            'align': 'center',
            'border': 1
        })

        cell_format = workbook.add_format({
            'border': 1,
            'align': 'center'
        })

        green = workbook.add_format({'color': 'green', 'bold': True})
        orange = workbook.add_format({'color': 'orange', 'bold': True})
        red = workbook.add_format({'color': 'red', 'bold': True})

        sheet.merge_range('A1:F1', 'Library Books Report', title_format)

        row = 2
        sheet.write(row, 0, 'Title', header_format)
        sheet.write(row, 1, 'Author', header_format)
        sheet.write(row, 2, 'Published Date', header_format)
        sheet.write(row, 3, 'Quantity', header_format)
        sheet.write(row, 4, 'Price', header_format)
        sheet.write(row, 5, 'Status', header_format)

        row += 1
        for book in books:

            if book.state == 'available':
                status_format = green
                status = 'Available'
            elif book.state == 'borrowed':
                status_format = orange
                status = 'Borrowed'
            else:
                status_format = red
                status = 'Out of Stock'

            sheet.write(row, 0, book.name or '', cell_format)
            sheet.write(row, 1, book.author or '', cell_format)
            sheet.write(row, 2, str(book.published_date or ''), cell_format)
            sheet.write(row, 3, book.quantity or 0, cell_format)
            sheet.write(row, 4, book.price_unit or 0, cell_format)
            sheet.write(row, 5, status, status_format)

            row += 1

        row += 2
        sheet.write(row, 0, 'Total Books:', header_format)
        sheet.write(row, 1, len(books), cell_format)

        workbook.close()

        output.seek(0)

        file_name = 'book_report.xlsx'

        return request.make_response(
            output.getvalue(),
            headers=[
                ('Content-type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename="{file_name}"'),
            ]
        )
