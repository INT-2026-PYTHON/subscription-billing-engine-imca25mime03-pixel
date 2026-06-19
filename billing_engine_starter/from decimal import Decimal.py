from decimal import Decimal

class Money:
    def __init__(self, amount: str, currency: str):
        self.amount = Decimal(amount)
        self.currency = currency

    def __add__(self, other):
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(str(self.amount + other.amount), self.currency)

    def __repr__(self):
        return f"{self.currency} {self.amount}"

if __name__ == "__main__":
    price = Money("0.10", "INR") + Money("0.20", "INR")
    print(price)  
