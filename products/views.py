from pyexpat.errors import messages
from django.shortcuts import redirect, render
from .models import Product

def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/product_list.html', {'products': products})


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        # Here, you can save it to a model or send email
        messages.success(request, "Thank you! Your message has been sent.")
        return redirect('contact')
    return render(request, 'products/contact.html')
