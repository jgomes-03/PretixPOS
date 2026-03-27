from decimal import Decimal

from pretix.base.models import Item, ItemVariation

from .base import ValidationError


class CartService:
    @staticmethod
    def compute_cart_totals(event, lines, discount=None):
        subtotal = Decimal('0.00')
        resolved_lines = []

        for line in lines:
            item = Item.objects.get(event=event, pk=line['item_id'])
            quantity = int(line.get('quantity', 1))
            variation_id = line.get('variation_id')
            variation = None
            unit_price = item.default_price

            if variation_id:
                variation = ItemVariation.objects.get(item=item, pk=variation_id)
                if variation.price is not None:
                    unit_price = variation.price

            if quantity <= 0:
                raise ValidationError('Quantity must be greater than zero')

            line_total = unit_price * quantity
            subtotal += line_total
            resolved_lines.append({
                'item_id': item.pk,
                'variation_id': variation.pk if variation else None,
                'quantity': quantity,
                'unit_price': str(unit_price),
                'line_total': str(line_total),
                'name': str(item.name),
            })

        discount_amount = Decimal('0.00')
        if discount:
            discount_amount = Decimal(str(discount.get('amount', '0.00')))
            if discount_amount < 0 or discount_amount > subtotal:
                raise ValidationError('Invalid discount amount')

        total = subtotal - discount_amount
        return {
            'lines': resolved_lines,
            'subtotal': str(subtotal),
            'discount': str(discount_amount),
            'total': str(total),
        }
