from django.shortcuts import render, get_object_or_404, redirect
from .forms import CartAddProductForm
from django.views.decorators.http import require_POST
from shop.models import Product
from .cart import Cart
from coupons.forms import CouponApplyForm
from shop.recommender import Recommender

@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product,
                 quantity=cd['quantity'],
                 override_quantity=cd['override'])
    return redirect('cart:cart_detail')

@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product=product)
    return redirect('cart:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={'quantity':item['quantity'],
                                                                   'override':True})
    coupon_apply_form = CouponApplyForm()

    r = Recommender()
    cart_products = [item['product'] for item in cart]
    recommended_products = r.suggested_products_for(cart_products, 2)
    return render(request, 
                  'cart/detail.html', 
                  {'cart':cart, 
                  'coupon_apply_form':coupon_apply_form,
                  'recommended_products':recommended_products})


