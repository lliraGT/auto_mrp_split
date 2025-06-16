# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ # type: ignore
from math import ceil
from odoo.exceptions import UserError # type: ignore
import json


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    is_special_product = fields.Boolean(
        string='Is Special Product',
        compute='_compute_is_special_product',
        store=True,
        help='Indicates if this production is for the special product that requires fixed batch splitting'
    )
    
    @api.depends('product_id')
    def _compute_is_special_product(self):
        # You can define multiple product IDs that require special handling
        target_product_ids = [4247, 4248, 4263, 4264, 4265, 4268, 123, 119]  # Add your product IDs here
        for record in self:
            if record.product_id and record.product_id.product_tmpl_id.id in target_product_ids:
                record.is_special_product = True
            else:
                record.is_special_product = False
    
    def action_auto_split_fixed_batches(self):
        """Custom action to split into fixed batch quantities"""
        self.ensure_one()
        
        if not self.is_special_product:
            raise UserError(_("This action can only be used with special products configured for batch splitting"))
        
        # Define batch rules based on product
        product_id = self.product_id.product_tmpl_id.id
        
        # Default values if no specific product match is found
        min_batches = 1
        fixed_qty_per_batch = 41.0
        
        # Product-specific batch rules
        if product_id == 4247:  # "Tortas Pollo Life Style"
            min_batches = 1
            fixed_qty_per_batch = 41.0
        elif product_id == 4248:  # "Bites Pollo Life Style"
            min_batches = 1
            fixed_qty_per_batch = 41.0
        elif product_id == 4263:  # "Tortas Res Life Style"
            min_batches = 1
            fixed_qty_per_batch = 41.0
        elif product_id == 4264:  # "Bites Res Life Style"
            min_batches = 1
            fixed_qty_per_batch = 41.0
        elif product_id == 4265:  # "Tortas Pavo Life Style"
            min_batches = 1
            fixed_qty_per_batch = 41.0
        elif product_id == 4268:  # "Bites Pavo Life Style"
            min_batches = 1
            fixed_qty_per_batch = 41.0
        elif product_id == 123:  # "Fit Sin Granos Mediana"
            min_batches = 1
            fixed_qty_per_batch = 41.0
        elif product_id == 119:  # "Baby KANI Mediana"
            min_batches = 1
            fixed_qty_per_batch = 41.0

        
        # Calculate how many batches we need to cover the total quantity
        # Just round up to the next integer (no minimum batches constraint)
        min_batches = 1
        required_batches = ceil(self.product_qty / fixed_qty_per_batch)
        
        # No rounding to multiples needed, just use the required number directly
        batches_needed = required_batches
        
        # Prepare the split quantities (all equal to fixed_qty_per_batch)
        split_quantities = [fixed_qty_per_batch] * batches_needed
        
        # Calculate the total that will be produced
        total_to_produce = sum(split_quantities)
        
        # Check if we'll overproduce and warn the user
        if total_to_produce > self.product_qty:
            return {
                'name': _('Overproduction Warning'),
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.auto.split.confirm',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_production_id': self.id,
                    'default_original_qty': self.product_qty,
                    'default_future_qty': total_to_produce,
                    'default_split_quantities': json.dumps(split_quantities),
                }
            }
        
        # If no overproduction, directly perform the split
        return self._perform_fixed_split(split_quantities)
    
    def _perform_fixed_split(self, split_quantities):
        """Split the production order into the specified quantities with proper component quantities"""
        self.ensure_one()
        
        # We'll create the new productions manually
        new_production_ids = []
        main_production = self
        original_qty = main_production.product_qty
        
        # Create production orders for all quantities except the last one
        for i, qty in enumerate(split_quantities[:-1]):
            # Copy the original production
            new_production = main_production.copy({
                'product_qty': qty,
                'name': f"{main_production.name}-{str(i+1).zfill(3)}",
            })
            
            # Update the move_raw_ids to have the correct component quantities
            # This is critical to ensure each split MO has the correct ingredient quantities
            ratio = qty / original_qty
            for move in new_production.move_raw_ids:
                move.product_uom_qty = move.product_uom_qty * ratio
            
            # Add to our list of new productions
            new_production_ids.append(new_production.id)
            
        # Update the original production with the last quantity
        main_production.write({
            'product_qty': split_quantities[-1],
            'name': f"{main_production.name}-{str(len(split_quantities)).zfill(3)}",
        })
        
        # Also update component quantities for the main production (now the last batch)
        ratio = split_quantities[-1] / original_qty
        for move in main_production.move_raw_ids:
            move.product_uom_qty = move.product_uom_qty * ratio
        
        # Add the main production to the list of productions
        new_production_ids.append(main_production.id)
        
        # Return an action to show the split productions
        return {
            'name': _('Split Productions'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', new_production_ids)],
            'target': 'current',
        }

class MrpAutoSplitConfirm(models.TransientModel):
    _name = 'mrp.auto.split.confirm'
    _description = 'Confirm Production Auto Split with Overproduction'
    
    production_id = fields.Many2one('mrp.production', string='Production Order', required=True)
    original_qty = fields.Float(string='Original Quantity')
    future_qty = fields.Float(string='Future Quantity')
    split_quantities = fields.Char(string='Split Quantities')
    
    def action_confirm_split(self):
        """Confirm the split operation despite overproduction"""
        self.ensure_one()
        
        # Parse the split quantities from the string representation
        split_quantities = json.loads(self.split_quantities)
        
        # Perform the split
        return self.production_id._perform_fixed_split(split_quantities)
    
    def action_cancel(self):
        """Cancel the split operation"""
        return {'type': 'ir.actions.act_window_close'}