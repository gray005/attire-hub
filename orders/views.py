import requests
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required




def _get_cart(request):
    """Retrieve cart from session"""
    return request.session.get('cart', {})

def _save_cart(request, cart):
    """Save updated cart to session"""
    request.session['cart'] = cart
    request.session.modified = True




def cart(request):
    """View user's cart"""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your cart.")
        return redirect('/accounts/login/')

    cart = _get_cart(request)
    if not cart:
        return render(request, 'orders/cart.html', {'items': [], 'total': 0})

    product_ids = [int(pid) for pid in cart.keys()]
    products = Product.objects.filter(id__in=product_ids)
    items = []
    total = 0

    for p in products:
        qty = cart.get(str(p.id), 0)
        line_total = p.price * qty
        total += line_total
        items.append({
            'product': p,
            'quantity': qty,
            'line_total': line_total,
        })

    return render(request, 'orders/cart.html', {'items': items, 'total': total})


@require_POST
def add_to_cart(request, product_id):
    """Add product to cart"""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to add items to your cart.")
        return redirect('/accounts/login/')

    cart = _get_cart(request)
    key = str(product_id)
    cart[key] = cart.get(key, 0) + 1
    _save_cart(request, cart)
    messages.success(request, "Item added to your cart successfully!")
    return redirect('cart')


@require_POST
def update_cart(request):
    """Update quantities in cart"""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to update your cart.")
        return redirect('/accounts/login/')

    cart = _get_cart(request)
    for key, value in request.POST.items():
        if key.startswith('qty-'):
            pid = key.split('qty-')[1]
            try:
                qty = int(value)
            except (ValueError, TypeError):
                qty = 0
            if qty > 0:
                cart[pid] = qty
            else:
                cart.pop(pid, None)
    _save_cart(request, cart)
    messages.success(request, "Cart updated successfully!")
    return redirect('cart')


@require_POST
def remove_from_cart(request, product_id):
    """Remove product from cart"""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to modify your cart.")
        return redirect('/accounts/login/')

    cart = _get_cart(request)
    cart.pop(str(product_id), None)
    _save_cart(request, cart)
    messages.success(request, "Item removed from your cart.")
    return redirect('cart')




def checkout(request):
    """Handle checkout and Paystack initialization"""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to proceed with checkout.")
        return redirect('/accounts/login/')

    cart = request.session.get('cart', {})
    items = []
    total_price = 0

    if cart:
        products = Product.objects.filter(id__in=[int(pid) for pid in cart.keys()])
        for product in products:
            quantity = cart.get(str(product.id), 0)
            subtotal = product.price * quantity
            total_price += subtotal
            items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })

    if request.method == 'POST':
        email = request.user.email or 'customer@example.com'
        amount = int(total_price * 100)  

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "email": email,
            "amount": amount,
            "callback_url": request.build_absolute_uri('/orders/verify/'),
        }

        
        response = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
        res_data = response.json()

        if res_data.get('status'):
            auth_url = res_data['data']['authorization_url']
            return redirect(auth_url)
        else:
            messages.error(request, "Payment initialization failed. Please try again.")

    context = {
        'items': items,
        'total_price': total_price,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
    }
    return render(request, 'orders/checkout.html', context)



def verify_payment(request):
    """Verify Paystack payment after redirection"""
    reference = request.GET.get('reference')

    if not reference:
        messages.error(request, "Payment reference not found.")
        return redirect('checkout')

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    url = f"https://api.paystack.co/transaction/verify/{reference}"
    response = requests.get(url, headers=headers)
    res_data = response.json()

    if res_data.get('status') and res_data['data']['status'] == 'success':
       
        request.session['cart'] = {}
        request.session.modified = True

        messages.success(request, "Payment verified successfully! Thank you for shopping with us 💜.")
        return redirect('order_success')
    else:
        messages.error(request, "Payment verification failed. Please try again or contact support.")
        return redirect('checkout')


def order_success(request):
    """Display success page after successful payment"""
    return render(request, 'orders/order_success.html')
