from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Order, OrderItem
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa

# Home page with categories & products
def home(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    return render(request, 'store/home.html', {'categories': categories, 'products': products})

# Show products by category
def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'store/category.html', {'category': category, 'products': products})

# Cart page
def cart(request):
    cart = request.session.get('cart', {})
    products = []
    total = 0
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        product.quantity = quantity
        product.subtotal = product.price * quantity
        total += product.subtotal
        products.append(product)
    return render(request, 'store/cart.html', {'products': products, 'total': total})

# Add to cart
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    return redirect('cart')

# Remove from cart
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
    request.session['cart'] = cart
    return redirect('cart')

# Checkout page
def checkout(request):
    cart = request.session.get('cart', {})
    if request.method == 'POST':
        full_name = request.POST['full_name']
        email = request.POST['email']
        phone = request.POST['phone']
        address = request.POST['address']

        total_amount = 0
        order = Order.objects.create(
            full_name=full_name, email=email, phone=phone,
            address=address, total_amount=0
        )

        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(order=order, product=product, quantity=quantity)
            total_amount += product.price * quantity

        order.total_amount = total_amount
        order.save()
        request.session['cart'] = {}  # empty cart after checkout
        return redirect('generate_invoice', order_id=order.id)
    else:
        products = []
        total = 0
        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            product.quantity = quantity
            product.subtotal = product.price * quantity
            total += product.subtotal
            products.append(product)
        return render(request, 'store/checkout.html', {'products': products, 'total': total})

# Generate PDF Invoice
def generate_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('store/invoice.html', {'order': order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response
