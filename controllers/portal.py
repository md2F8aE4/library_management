from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class LibraryPortal(http.Controller):

    def _get_library_member(self, partner):
        if not partner:
            return None
        member = request.env['library.member'].sudo().search([('partner_id', '=', partner.id)], limit=1)
        if not member:
            member = request.env['library.member'].sudo().create({
                'partner_id': partner.id,
                'name': partner.name,
                'email': partner.email,
                'phone': partner.phone,
            })
        return member

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
        member = self._get_library_member(partner)

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
    



    @http.route(['/my/borrowed_books'], type='http', auth="user", website=True)
    def portal_my_borrowed_books(self, **kw):
        partner = request.env.user.partner_id
        member = self._get_library_member(partner)
        if member:
            borrowed = request.env['borrow.book'].sudo().search([
                ('member_id', '=', member.id),
                ('state', '=', 'borrowed')
            ])
            books = borrowed.mapped('book_id')
        else:
            books = request.env['library.book'].browse([])

        return request.render('library_management.portal_my_borrowed_books', {'books': books})


class LibraryCustomerPortal(CustomerPortal):

    @http.route(['/my/orders', '/my/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, **kwargs):
        return request.redirect('/my/borrowed_books')