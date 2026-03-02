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
     price_unit = fields.Float(string='Unit Price', related='product_id.list_price', store=True)                       # خليت السعر يتخزن علشان ما يتغيرش بعدين
     state = fields.Selection([ ('available','Available'), ('borrowed','Borrowed'), ('returned','Returned') ], default='available') 
     customer_id = fields.Many2one('res.partner', string='Customer')             # هنا عدلت  customer 
     availability = fields.Char(compute="_compute_availability", store=True)
     delivery_id = fields.Many2one('stock.picking')
     invoice_id = fields.Many2one('account.move')
     delivery_count = fields.Integer(compute="_compute_counts", store=True)
     invoice_count = fields.Integer(compute="_compute_counts", store=True)
<<<<<<< HEAD

     
=======
     
      
     @api.depends('delivery_id', 'invoice_id')                                                                      
>>>>>>> d77d0c2 (Update project files)
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
     def _check_quantity_rules(self):
      for record in self:
        if record.quantity <= 0:                                   #وخليت هنا الكميه تكون صفر او اكبر عشان متبقاش بلسالب 
            raise ValidationError("Quantity must be greater than zero.")

        if record.product_id and record.quantity > record.product_id.qty_available:
            raise ValidationError("Not enough stock.")
    

     def action_borrow(self):                     # زرار علشان أستعير الكتاب
          self.ensure_one()                        # علشان أشتغل على سجل واحد بس
          if self.state == 'borrowed':         # علشان ما أستعيرش الكتاب مرتين
           raise ValidationError("Book is already borrowed.")

          if not self.product_id:      # لازم المنتج يكون موجود 
            raise ValidationError("Product is required.")

          if not self.customer_id:          #عشان العميل 
             raise ValidationError("Customer is required.")

          if self.quantity > self.product_id.qty_available:
            raise ValidationError("Not enough stock.")

          picking = self.env['stock.picking'].create({
            'partner_id': self.customer_id.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'move_ids_without_package': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': self.quantity,
                'product_uom': self.product_id.uom_id.id,
                'name': self.product_id.name,
            })]
        })

          picking.action_confirm()
          picking.button_validate()
  
          invoice = self.env['account.move'].create({              # علشان أعمل الفاتورة
            'move_type': 'out_invoice',
            'partner_id': self.customer_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'quantity': self.quantity,
                'price_unit': self.price_unit,
            })]
        })

          invoice.action_post()
                                   # علشان اخلي  الفاتوره والتوصيل يكون بلكتاب
          self.delivery_id = picking.id    
          self.invoice_id = invoice.id
          self.state = 'borrowed'

     def action_view_delivery(self):
      self.ensure_one()
      if not self.delivery_id:
        raise ValidationError("No delivery found.")    #لو مفيش توصيل
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
         raise ValidationError("No invoice found.")             #لو مفيش فاتورة
      return {
            
        'type': 'ir.actions.act_window',
        'name': 'Invoice',
        'res_model': 'account.move',
        'view_mode': 'form',
        'res_id': self.invoice_id.id
    }