from odoo import fields , models,api
from datetime import date
from odoo.exceptions import ValidationError

class borrowbook(models.Model):
    _name= "borrow.book"
    _description = 'Library Borrow Transaction'
    _inherit=['mail.thread','mail.activity.mixin']

    name = fields.Char(default='New', readonly=True, copy=False)
    member_id= fields.Many2one('library.member')
    book_id= fields.Many2one('library.book')
    borrow_date= fields.Date(default=fields.Date.today)
    due_date= fields.Date()
    return_date= fields.Date()
    quantity = fields.Integer(default=1)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled')
    ], default='draft', string="Status")

    late_days= fields.Integer(compute="_compute_late_days")
    fine_amount= fields.Float(compute="_compute_fine")

    invoice_id= fields.Many2one('account.move')
    delivery_id= fields.Many2one('stock.picking')
    return_picking_id= fields.Many2one('stock.picking')
    daily_fine=fields.Float(string='daily fine',default=5) 
    
   
    @api.depends('due_date', 'return_date')
    def _compute_late_days(self):
        for record in self:
            if record.return_date and record.due_date:
                late = (record.return_date - record.due_date).days
                record.late_days = late if late > 0 else 0
            else:
                record.late_days = 0

    @api.depends('late_days','daily_fine')
    def _compute_fine(self):
        for record in self:
            record.fine_amount = record.late_days * record.daily_fine

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('name_sequence') or 'New'
        return super().create(vals_list)

    def action_set_draft(self):
        self.state = 'draft'

    def action_set_borrowed(self):
        for rec in self:

            if rec.state =='cancelled':
                raise ValidationError("Cancelled transaction cannot be borrowed")

            if rec.state=='borrowed':
                raise ValidationError("This transaction is already borrowed")
            
            if not rec.member_id:
                raise ValidationError("Select member")

            if not rec.member_id.active:
                raise ValidationError("Member is not active")

            if not rec.book_id:
                raise ValidationError("Select book")

            if rec.book_id.quantity < rec.quantity:
                raise ValidationError("Not enough quantity")

            picking = self.env['stock.picking'].create({
             'partner_id': rec.member_id.partner_id.id,
             'picking_type_id': self.env.ref('stock.picking_type_out').id,
             'location_id': self.env.ref('stock.stock_location_stock').id,
             'location_dest_id': rec.member_id.partner_id.property_stock_customer.id,
})

            rec.delivery_id = picking.id
            rec.state = 'borrowed'

    def action_set_returned(self):
        for rec in self:

            if rec.state == 'cancelled':
             raise ValidationError("Cancelled transaction cannot be returned")

            if rec.state == 'returned':
             raise ValidationError("This transaction is already returned")
           
            rec.return_date = fields.Date.today()

            picking = self.env['stock.picking'].create({
                'partner_id': rec.member_id.partner_id.id,
                'picking_type_id': self.env.ref('stock.picking_type_in').id,
                'location_id': self.env.ref('stock.stock_location_customers').id,
                'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            })

            rec.return_picking_id = picking.id
            rec.state = 'returned'

    def action_set_overdue(self):
        self.state = 'overdue'

    def check_overdue(self):
        today = fields.Date.today()

        records = self.search([
            ('state', '=', 'borrowed'),
            ('due_date', '<', today),
            ('return_date', '=', False)
        ])

        records.write({'state': 'overdue'})

    def action_set_cancelled(self):
        self.state = 'cancelled'    


    def action_view_delivery(self):
        self.ensure_one()
        return {
            'name': 'Delivery Order',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.delivery_id.id,
            'target': 'current',
        }

    def action_view_return(self):
        self.ensure_one()
        return {
            'name': 'Return Picking',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.return_picking_id.id,
            'target': 'current',
        }

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'target': 'current',
        }    