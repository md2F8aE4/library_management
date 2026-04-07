from odoo import api, fields, models


class LibraryMember(models.Model):
    _name = 'library.member'
    _description = 'Library Member'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Member')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone No')
    member_code = fields.Char(string='Member Code', default='New', copy=False, readonly=True)
    partner_id = fields.Many2one('res.partner')
    membership_date = fields.Date(string='Date')
    active = fields.Boolean(default=True, )
    notes = fields.Text()
    borrow_count = fields.Integer( compute='_compute_borrow_count')
    borrow_ids = fields.One2many('borrow.book', 'member_id', string='Borrow Records')
    active_borrow_count = fields.Integer(
        string="Active Borrowed Books",
        compute="_compute_borrow_stats"
    )

    overdue_count = fields.Integer(
        string="Overdue Books",
        compute="_compute_borrow_stats"
    )


    @api.depends('borrow_ids.state')
    def _compute_borrow_stats(self):
        for rec in self:

            active = self.env['borrow.book'].search_count([
                ('member_id', '=', rec.id),
                ('state', '=', 'borrowed')
            ])

            overdue = self.env['borrow.book'].search_count([
                ('member_id', '=', rec.id),
                ('state', '=', 'overdue')
            ])

            rec.active_borrow_count = active
            rec.overdue_count = overdue
    @api.depends('borrow_ids')        
    def _compute_borrow_count(self):
        for member in self:
            member.borrow_count=self.env['borrow.book'].search_count([('member_id', '=', member.id)])
   
    def action_view_borrowing_history(self):
        self.ensure_one()
        return {
            'name': 'Borrowing History',
            'type': 'ir.actions.act_window',
            'res_model': 'borrow.book',
            'view_mode': 'tree,form',
            'domain': [('member_id', '=', self.id)],
            'target': 'current',
        }
   

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('member_code') or vals.get('member_code') == 'New':
                vals['member_code'] = self.env['ir.sequence'].next_by_code('member_sequence') or 'New'
            partner_id = vals.get('partner_id')
            if partner_id and not (vals.get('name') or vals.get('email') or vals.get('phone')):
                partner = self.env['res.partner'].browse(partner_id)
                vals.setdefault('name', partner.name)
                vals.setdefault('email', partner.email)
                vals.setdefault('phone', partner.phone)
        return super().create(vals_list)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.name = self.partner_id.name or False
            self.email = self.partner_id.email or False
            self.phone = self.partner_id.phone or False
