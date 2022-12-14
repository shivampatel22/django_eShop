from django.conf import settings
from shop.models import Product
from decimal import Decimal
from coupons.models import Coupon 

class Cart(object):
    
    def __init__(self, request):
        # get the current session
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        # create a cart in the session if not present
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        # get the applied coupon
        self.coupon_id = self.session.get('coupon_id')

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products
        from the database.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        # deep copy of self.cart
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            # return item and resume at the previous state of generator function
            yield item
    
    def __len__(self):
        # return count of total quantity in cart
        return sum(item['quantity'] for item in self.cart.values())

    def add(self, product, quantity=1, override_quantity=False):
        # convert id to str for serialization
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity':0,
                                     'price':str(product.price)}
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def remove(self, product):
        product_id = str(product.id)
        # remove the key of product from cart
        if product_id in self.cart:
            del self.cart[product_id]
        self.save()
    
    def clear(self):
        # clear the cart
        del self.session[settings.CART_SESSION_ID]
        # remove coupon from session
        coupon_id = self.session.get('coupon_id', None)
        if coupon_id:
            del self.session['coupon_id']
        self.save()

    def save(self):
        # mark the session as modified
        self.session.modified = True

    def get_total_price(self):
        # return total price of cart
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    @property
    def coupon(self):
        """
        return coupon object if coupon id is
        set in session
        """
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
                pass
        return None

    def get_discount(self):
        if self.coupon:
            return((self.coupon.discount / Decimal(100)) * self.get_total_price())
        return Decimal(0)

    def get_total_price_after_discount(self):
        return self.get_total_price() - self.get_discount()
    
    

