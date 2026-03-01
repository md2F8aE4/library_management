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
     price_unit = fields.Float(string='Unit Price', related='product_id.list_price') 
     state = fields.Selection([ ('available','Available'), ('borrowed','Borrowed'), ('returned','Returned') ], default='available') 
     customr_id = fields.Many2one('res.partner', string='Customer')
     availability = fields.Char(compute="_compute_availability", store=True)
     delivery_id = fields.Many2one('stock.picking')
     invoice_id = fields.Many2one('account.move')
     delivery_count = fields.Integer(compute="_compute_counts", store=True)
     invoice_count = fields.Integer(compute="_compute_counts", store=True)
     def _compute_counts(self):
      for record in self:
        record.delivery_count = 1 if record.delivery_id else 0
        record.invoice_count = 1 if record.invoice_id else 0
    
    
     @api.depends('product_id','quantity')
     def _compute_availability(self):
      for record in self:
        if record.product_id and record.quantity <= record.product_id.qty_available:
            record.availability = "Available"
        else:
            record.availability = "Out of Stock"
    

     @api.constrains('product_id', 'quantity') 
     def _check_stock_quantity(self): 
         for record in self:
             if record.product_id and record.quantity > record.product_id.qty_available:
                 raise ValidationError("Not enough stock .")
     def write(self, vals):

      res = super().write(vals)

      for record in self:

        if record.state == 'borrowed':

            if record.quantity > record.product_id.qty_available:
                raise ValidationError("Not enough stock")

            picking = self.env['stock.picking'].create({
                'partner_id': record.customer_id.id,
                'picking_type_id': self.env.ref('stock.picking_type_out').id,
                'move_ids': [(0, 0, {
                    'product_id': record.product_id.id,
                    'product_uom_qty': record.quantity,
                    'product_uom': record.product_id.uom_id.id,
                })]
            })

            picking.action_confirm()
            picking.button_validate()

            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': record.customer_id.id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': record.product_id.id,
                    'quantity': record.quantity,
                    'price_unit': record.price_unit,
                })]
            })

            invoice.action_post()

        return res



     def action_view_delivery(self):
      return {
        'type': 'ir.actions.act_window',
        'name': 'Delivery',
        'res_model': 'stock.picking',
        'view_mode': 'form',
        'res_id': self.delivery_id.id
    }
     

     def action_view_invoice(self):
      return {
        'type': 'ir.actions.act_window',
        'name': 'Invoice',
        'res_model': 'account.move',
        'view_mode': 'form',
        'res_id': self.invoice_id.id
    }