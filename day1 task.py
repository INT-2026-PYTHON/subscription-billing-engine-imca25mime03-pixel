from decimal import Decimal
from billing_engine.money import Money
from billing_engine.pricing import Tier, TieredPricing

tiers = [
    Tier(from_units=0, to_units=1000, unit_price=Money("2.00", "INR")),
    Tier(from_units=1000, to_units=None, unit_price=Money("1.50", "INR")),
]

pricing = TieredPricing(tiers)

quantity = 2500
total = pricing.calculate(quantity)

print(f"Quantity: {quantity}")
print(f"Total: {total}")  

