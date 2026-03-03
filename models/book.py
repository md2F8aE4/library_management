from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Book(models.Model):
    _name = 'library.book'
    _description = 'Book'

    name = fields.Char(string='Book Name')
    author = fields.Char(string='Author Name')
    published_date = fields.Date(string='Published Date')
    description = fields.Text(string='Description')
    product_id = fields.Many2one('product.product', string='Related Product', domain=[('detailed_type', '=', 'product')])
    quantity = fields.Float(string='Quantity', default=1)
    price_unit = fields.Float(string='Unit Price', related='product_id.list_price', store=True)
    state = fields.Selection([('available', 'Available'), ('borrowed', 'Borrowed'), ('returned', 'Returned')], default='available')
    customer_id = fields.Many2one('res.partner', string='Customer')
    availability = fields.Char(compute="_compute_availability", store=True)
    delivery_id = fields.Many2one('stock.picking')
    invoice_id = fields.Many2one('account.move')
    delivery_count = fields.Integer(compute="_compute_counts", store=True)
    invoice_count = fields.Integer(compute="_compute_counts", store=True)

    @api.depends('delivery_id', 'invoice_id')
    def _compute_counts(self):
        for record in self:
            record.delivery_count = 1 if record.delivery_id else 0
            record.invoice_count = 1 if record.invoice_id else 0

    @api.depends('product_id', 'quantity')
    def _compute_availability(self):
        for record in self:
            if record.product_id and record.quantity <= record.product_id.qty_available:
                record.availability = "Available"
            else:
                record.availability = "Out of Stock"

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

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'quantity': self.quantity,
                'price_unit': self.price_unit,
            })]
        })

        invoice.action_post()
        self.delivery_id = picking.id
        self.invoice_id = invoice.id
        self.state = 'borrowed'

    def action_view_delivery(self):
        self.ensure_one()
        if not self.delivery_id:
            raise ValidationError("No delivery found.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Delivery',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.delivery_id.id
        }

    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise ValidationError("No invoice found.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id
        }

    def action_set_available(self):
        self.state = 'available'

    def action_set_borrowed(self):
        self.state = 'borrowed'

    def action_set_returned(self):
        self.state = 'returned'
