from odoo import api, fields, models

class BorrowBookWizard(models.TransientModel):
    _name = 'borrow.book.wizard'
    _description = 'Borrow Book Wizard'

    member_id = fields.Many2one('library.member', string="Member", required=True)
    book_id = fields.Many2one('library.book', string="Book")
    quantity = fields.Integer(string="Quantity", required=True)

    def action_confirm(self):
   
        self.env['borrow.book'].create({
            'member_id': self.member_id.id,
            'book_id': self.book_id.id,
            'quantity': self.quantity,
            'state': 'borrowed'
        })
    
        self.book_id.state = 'borrowed'
        return {'type': 'ir.actions.act_window_close'}