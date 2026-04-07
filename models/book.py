from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Book(models.Model):
    _name = 'library.book'
    _description = 'Book'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Book Name',tracking=True)
    author = fields.Char(string='Author Name',tracking=True)
    published_date = fields.Date(string='Published Date',tracking=True)
    description = fields.Text(string='Description')
    product_id = fields.Many2one('product.product', string='Related Product', domain=[('detailed_type', '=', 'product')])
    quantity = fields.Float(string='Quantity', default=1)
    price_unit = fields.Float(string='Unit Price', related='product_id.list_price', store=True)
    state = fields.Selection(
        [
            ('available', 'Available'),
            ('borrowed', 'Borrowed'),
            ('out_of_stock', 'Out of Stock'),
        ],
        compute='_compute_state',
        store=True,
        string='Status',
    )
    customer_id = fields.Many2one('res.partner', string='Customer')
    availability = fields.Char(compute="_compute_availability", store=True)
    delivery_id = fields.Many2one('stock.picking')
    invoice_id = fields.Many2one('account.move')
    delivery_count = fields.Integer(compute="_compute_counts", store=True)
    invoice_count = fields.Integer(compute="_compute_invoice_count", store=True)
    borrow_ids = fields.One2many('borrow.book', 'book_id', string='Borrow Records')
    borrow_count = fields.Integer( compute='_compute_borrow_count', store=True)
    
    current_borrower_id = fields.Many2one('library.member', string="Current Borrower",compute="_compute_current_borrower")

    @api.depends('borrow_ids.state')
    def _compute_current_borrower(self):
        for rec in self:
            borrow = self.env['borrow.book'].search([
                ('book_id', '=', rec.id),
                ('state', '=', 'borrowed')
            ], limit=1)

            rec.current_borrower_id = borrow.member_id

    @api.depends('borrow_ids')
    def _compute_borrow_count(self):
        for book in self:
            book.borrow_count = self.env['borrow.book'].search_count([('book_id', '=', book.id)])

    def action_view_borrow_history(self):
        self.ensure_one()
        return {
            'name': 'Borrow History',
            'type': 'ir.actions.act_window',
            'res_model': 'borrow.book',
            'view_mode': 'tree,form',
            'domain': [('book_id', '=', self.id)],
            'target': 'current',
        }
   
   
    @api.depends('invoice_id')
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = 1 if record.invoice_id else 0

    @api.depends('product_id', 'quantity')
    def _compute_availability(self):
        for record in self:
            if record.product_id and record.quantity <= record.product_id.qty_available:
                record.availability = "Available"
            else:
                record.availability = "Out of Stock"

    @api.depends('borrow_ids.state', 'product_id.qty_available', 'quantity')
    def _compute_state(self):
        for book in self:
            active_borrows = book.borrow_ids.filtered(
                lambda b: b.state in ('borrowed', 'overdue')
            )
            if active_borrows:
                book.state = 'borrowed'
            elif book.product_id and book.product_id.qty_available <= 0:
                book.state = 'out_of_stock'
            else:
                book.state = 'available'

    @api.constrains('product_id', 'quantity')
    def _check_quantity_rules(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError("Quantity must be greater than zero.")
            if record.product_id and record.quantity > record.product_id.qty_available:
                raise ValidationError("Not enough stock.")

    def action_borrow(self):
        self.ensure_one()
        if self.state == 'borrowed':
            raise ValidationError("Book is already borrowed.")
        if not self.product_id:
            raise ValidationError("Product is required.")
        if not self.customer_id:
            raise ValidationError("Customer is required.")
        if self.quantity > self.product_id.qty_available:
            raise ValidationError("Not enough stock.")

        picking_type = self.env.ref('stock.picking_type_out')
        source_location = picking_type.default_location_src_id or self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        dest_location = picking_type.default_location_dest_id or self.env.ref('stock.stock_location_customers', raise_if_not_found=False)
        if not source_location or not dest_location:
            raise ValidationError("Please configure Source and Destination locations for Delivery Orders.")

        picking = self.env['stock.picking'].create({
            'partner_id': self.customer_id.id,
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': dest_location.id,
            'move_ids_without_package': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': self.quantity,
                'product_uom': self.product_id.uom_id.id,
                'name': self.product_id.name,
                'location_id': source_location.id,
                'location_dest_id': dest_location.id,
            })]
        })

        picking.action_confirm()
        picking.button_validate()

      

    def action_view_customer_invoices(self):
        self.ensure_one() 
        return {
            'name': 'Customer Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move', 
            'view_mode': 'form',    
            'domain': [('partner_id', '=', self.customer_id.id)], 
            'context': {'default_move_type': 'out_invoice', 'default_partner_id': self.customer_id.id},
                    
        }   


    def action_open_borrow_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Borrow Book',
            'res_model': 'borrow.book.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_book_id': self.id}
        }
