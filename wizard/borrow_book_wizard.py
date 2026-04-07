from odoo import api, fields, models
from datetime import timedelta 

class BorrowBookWizard(models.TransientModel):
    _name = 'borrow.book.wizard'
    _description = 'Borrow Book Wizard'

    member_id = fields.Many2one('library.member', string="Member", required=True)
    book_id = fields.Many2one('library.book', string="Book")
    quantity = fields.Integer(string="Quantity", required=True)
    due_date = fields.Date(
      string="Due Date",
       default=lambda self: fields.Date.today() + timedelta(days=14)
            )

    def action_confirm(self):
   
        borrow = self.env['borrow.book'].create({
            'member_id': self.member_id.id,
            'book_id': self.book_id.id,
            'quantity': self.quantity,
            'due_date': self.due_date,
        })
    
        borrow.action_set_borrowed()
        return {'type': 'ir.actions.act_window_close'}
