from odoo import http
from odoo.http import request


class LibraryPortal(http.Controller):

    @http.route(['/my/books'], type='http', auth="user", website=True)
    def portal_my_books(self, **kw):
        books = request.env['library.book'].sudo().search([])
        return request.render('library_management.portal_my_books', {
            'books': books
        })

    @http.route(['/my/book/borrow/<int:book_id>'], type='http', auth="user", website=True)
    def borrow_book(self, book_id, **kw):
        book = request.env['library.book'].sudo().browse(book_id)
        partner = request.env.user.partner_id

        member = request.env['library.member'].sudo().search([
            ('partner_id', '=', partner.id)
        ], limit=1)

        if not member or book.state != 'available':
            return request.redirect('/my/books')

        request.env['borrow.book'].sudo().create({
            'book_id': book.id,
            'member_id': member.id,
            'state': 'borrowed'
        })
        book.sudo().write({
    'state': 'borrowed'
})

        return request.redirect('/my/books')
    


    @http.route(['/my/book/return/<int:book_id>'], type='http', auth="user", website=True)
    def return_book(self, book_id, **kw):

        book = request.env['library.book'].sudo().browse(book_id)

        borrow = request.env['borrow.book'].sudo().search([
        ('book_id', '=', book.id),
        ('state', '=', 'borrowed')
    ], limit=1)

        if borrow:
         borrow.write({'state': 'returned'})
        book.write({'state': 'available'})

        return request.redirect('/my/books')