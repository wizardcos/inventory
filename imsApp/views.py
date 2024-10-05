from email import message
import os
from unicodedata import category
from unittest import loader
from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from ims_django.settings import MEDIA_ROOT, MEDIA_URL
import json
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import letter
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from imsApp.forms import SaveStock, UserRegistration, UpdateProfile, UpdatePasswords, SaveCategory, SaveProduct, SaveInvoice, SaveInvoiceItem,PoleTransactionForm
from imsApp.models import Category, Product, Stock,PoleTransaction, Invoice, Invoice_Item
from cryptography.fernet import Fernet
from django.conf import settings
import base64

context = {
    'page_title' : 'INVENTORY Management System',
}
#login
def login_user(request):
    logout(request)
    resp = {"status":'failed','msg':''}
    username = ''
    password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                resp['status']='success'
            else:
                resp['msg'] = "Incorrect username or password"
        else:
            resp['msg'] = "Incorrect username or password"
    return HttpResponse(json.dumps(resp),content_type='application/json')

#Logout
def logoutuser(request):
    logout(request)
    return redirect('/')

@login_required
def home(request):
    # Get data for invoices and pole transactions
    invoices = Invoice.objects.all()
    pole_transactions = PoleTransaction.objects.all()
    
    # Prepare overview data
    overview_data = [
        {
            'name': invoice.order_type,
            'owner': invoice.customer,
            'status': invoice.status,
            'due_date': invoice.date_created,
            'priority': invoice.total,
            'progress': 75
        } for invoice in invoices
    ] + [
        {
            'name': pole.order_type,
            'owner': pole.customer,
            'status': pole.status,
            'due_date': pole.date_created,
            'priority': pole.quantity,
            'progress': 50
        } for pole in pole_transactions
    ]

    # Prepare context data
    context = {
        'overview_data': overview_data,
        'page_title': 'Home',
        'categories': Category.objects.count(),
        'products': Product.objects.count(),
        'sales': Invoice.objects.count(),
    }
    
    # Render the home.html template
    return render(request, 'home.html', context)


def registerUser(request):
    user = request.user
    if user.is_authenticated:
        return redirect('home-page')
    context['page_title'] = "Register User"
    if request.method == 'POST':
        data = request.POST
        form = UserRegistration(data)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            pwd = form.cleaned_data.get('password1')
            loginUser = authenticate(username= username, password = pwd)
            login(request, loginUser)
            return redirect('home-page')
        else:
            context['reg_form'] = form

    return render(request,'register.html',context)

@login_required
def update_profile(request):
    context['page_title'] = 'Update Profile'
    user = User.objects.get(id = request.user.id)
    if not request.method == 'POST':
        form = UpdateProfile(instance=user)
        context['form'] = form
        print(form)
    else:
        form = UpdateProfile(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile has been updated")
            return redirect("profile")
        else:
            context['form'] = form
            
    return render(request, 'manage_profile.html',context)


@login_required
def update_password(request):
    context['page_title'] = "Update Password"
    if request.method == 'POST':
        form = UpdatePasswords(user = request.user, data= request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Your Account Password has been updated successfully")
            update_session_auth_hash(request, form.user)
            return redirect("profile")
        else:
            context['form'] = form
    else:
        form = UpdatePasswords(request.POST)
        context['form'] = form
    return render(request,'update_password.html',context)


@login_required
def profile(request):
    context['page_title'] = 'Profile'
    return render(request, 'profile.html',context)


# Category
@login_required
def category_mgt(request):
    context['page_title'] = "Product Categories"
    categories = Category.objects.all()
    context['categories'] = categories
    return render(request, 'category_mgt.html', context)

@login_required
def save_category(request):
    resp = {'status':'failed','msg':''}
    if request.method == 'POST':
        if (request.POST['id']).isnumeric():
            category = Category.objects.get(pk=request.POST['id'])
        else:
            category = None
        if category is None:
            form = SaveCategory(request.POST)
        else:
            form = SaveCategory(request.POST, instance= category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category has been saved successfully.')
            resp['status'] = 'success'
        else:
            for fields in form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")
    else:
        resp['msg'] = 'No data has been sent.'
    return HttpResponse(json.dumps(resp), content_type = 'application/json')

@login_required
def manage_category(request, pk=None):
    context['page_title'] = "Manage Category"
    if not pk is None:
        category = Category.objects.get(id = pk)
        context['category'] = category
    else:
        context['category'] = {}

    return render(request, 'manage_category.html', context)

@login_required
def delete_category(request):
    resp = {'status':'failed', 'msg':''}

    if request.method == 'POST':
        try:
            category = Category.objects.get(id = request.POST['id'])
            category.delete()
            messages.success(request, 'Category has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Category has failed to delete'
            print(err)
    else:
        resp['msg'] = 'Category has failed to delete'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")
        
# product
@login_required
def product_mgt(request):
    context['page_title'] = "Product List"
    products = Product.objects.all()
    context['products'] = products

    return render(request, 'product_mgt.html', context)

@login_required
def save_product(request):
    resp = {'status':'failed','msg':''}
    if request.method == 'POST':
        if (request.POST['id']).isnumeric():
            product = Product.objects.get(pk=request.POST['id'])
        else:
            product = None
        if product is None:
            form = SaveProduct(request.POST)
        else:
            form = SaveProduct(request.POST, instance= product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product has been saved successfully.')
            resp['status'] = 'success'
        else:
            for fields in form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")
    else:
        resp['msg'] = 'No data has been sent.'
    return HttpResponse(json.dumps(resp), content_type = 'application/json')

@login_required
def manage_product(request, pk=None):
    context['page_title'] = "Manage Product"
    if not pk is None:
        product = Product.objects.get(id = pk)
        context['product'] = product
    else:
        context['product'] = {}

    return render(request, 'manage_product.html', context)

@login_required
def delete_product(request):
    resp = {'status':'failed', 'msg':''}

    if request.method == 'POST':
        try:
            product = Product.objects.get(id = request.POST['id'])
            product.delete()
            messages.success(request, 'Product has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Product has failed to delete'
            print(err)

    else:
        resp['msg'] = 'Product has failed to delete'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def inventory(request):
    # Initialize the context dictionary
    context = {}
    context['page_title'] = 'Inventory'
    products = Product.objects.all()
    context['products'] = products
    return render(request, 'inventory.html', context)

#Inventory History
@login_required
def inv_history(request, pk= None):
    context['page_title'] = 'Inventory History'
    if pk is None:
        messages.error(request, "Product ID is not recognized")
        return redirect('inventory-page')
    else:
        product = Product.objects.get(id = pk)
        stocks = Stock.objects.filter(product = product).all()
        context['product'] = product
        context['stocks'] = stocks

        return render(request, 'inventory-history.html', context )

#Stock Form
@login_required
def manage_stock(request,pid = None ,pk = None):
    if pid is None:
        messages.error(request, "Product ID is not recognized")
        return redirect('inventory-page')
    context['pid'] = pid
    if pk is None:
        context['page_title'] = "Add New Stock"
        context['stock'] = {}
    else:
        context['page_title'] = "Manage New Stock"
        stock = Stock.objects.get(id = pk)
        context['stock'] = stock
    
    return render(request, 'manage_stock.html', context )

@login_required
def save_stock(request):
    resp = {'status':'failed','msg':''}
    if request.method == 'POST':
        if (request.POST['id']).isnumeric():
            stock = Stock.objects.get(pk=request.POST['id'])
        else:
            stock = None
        if stock is None:
            form = SaveStock(request.POST)
        else:
            form = SaveStock(request.POST, instance= stock)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stock has been saved successfully.')
            resp['status'] = 'success'
        else:
            for fields in form:
                for error in fields.errors:
                    resp['msg'] += str(error + "<br>")
    else:
        resp['msg'] = 'No data has been sent.'
    return HttpResponse(json.dumps(resp), content_type = 'application/json')

@login_required
def delete_stock(request):
    resp = {'status':'failed', 'msg':''}

    if request.method == 'POST':
        try:
            stock = Stock.objects.get(id = request.POST['id'])
            stock.delete()
            messages.success(request, 'Stock has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Stock has failed to delete'
            print(err)

    else:
        resp['msg'] = 'Stock has failed to delete'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def sales_mgt(request):
    categories = Category.objects.prefetch_related('products').all()
    return render(request, 'sales.html', {'categories': categories})
    


def get_product(request,pk = None):
    resp = {'status':'failed','data':{},'msg':''}
    if pk is None:
        resp['msg'] = 'Product ID is not recognized'
    else:
        product = Product.objects.get(id = pk)
        resp['data']['product'] = str(product.code + " - " + product.name)
        resp['data']['id'] = product.id
        resp['data']['price'] = product.price
        resp['status'] = 'success'
    
    return HttpResponse(json.dumps(resp),content_type="application/json")



@login_required
def save_sales(request):
    resp = {'status': 'failed', 'msg': ''}
    
    if request.method == 'POST':
        pids = request.POST.getlist('pid[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price[]')
        
        invoice_form = SaveInvoice(request.POST)
        if invoice_form.is_valid():
            invoice = invoice_form.save()
            
            # Loop through each product with its corresponding quantity and price
            for idx, pid in enumerate(pids):
                product_data = {
                    'invoice': invoice.id,
                    'product': pid,
                    'quantity': quantities[idx],  # Get the quantity corresponding to the current product
                    'price': prices[idx]  # Get the price corresponding to the current product
                }
                ii_form = SaveInvoiceItem(product_data)
                
                if ii_form.is_valid():
                    ii_form.save()
                else:
                    invoice.delete()  # Rollback invoice if any product fails to save
                    resp['msg'] = ii_form.errors
                    break
            else:
                messages.success(request, "Sale Transaction has been saved.")
                resp['status'] = 'success'
        else:
            resp['msg'] = invoice_form.errors
    
    return JsonResponse(resp)
@login_required
def invoices(request):
    invoice =  Invoice.objects.all()
    context['page_title'] = 'Invoices'
    context['invoices'] = invoice
    return render(request, 'invoices.html', context)

@login_required
def invoice_history(request, pk=None):
    if pk is not None:
        invoice = get_object_or_404(Invoice, pk=pk)
        invoice_items = Invoice_Item.objects.filter(invoice=invoice)
        context['invoice'] = invoice
        context['invoice_items'] = invoice_items
    context['page_title'] = 'Project History'
    return render(request, 'project-history.html', context)


@login_required
def delete_invoice(request):
    resp = {'status':'failed', 'msg':''}

    if request.method == 'POST':
        try:
            invoice = Invoice.objects.get(id = request.POST['id'])
            invoice.delete()
            messages.success(request, 'Invoice has been deleted successfully')
            resp['status'] = 'success'
        except Exception as err:
            resp['msg'] = 'Invoice has failed to delete'
            print(err)

    else:
        resp['msg'] = 'Invoice has failed to delete'
    
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def pole(request, pk=None):
    transactions = PoleTransaction.objects.all()
    return render(request, 'poles-transaction.html', {'transactions': transactions})

@login_required
def save_transaction(request):
    if request.method == 'POST':
     
        pipes = [request.POST.get(f'pipe{i}') for i in range(1, 7)]
        arms = [request.POST.get(f'arm{i}') for i in range(1, 4)]
        paint = [request.POST.get(f'paint{i}') for i in range(1, 4)]
     
        data = {
            'customer': request.POST['customer'],
            'customer_code': request.POST['customer_code'],
            'order_type': request.POST['order_type'],
            'product_name': request.POST['product_name'],
            'quantity': request.POST['quantity'],
            'description': request.POST['description'],
            'pipes': pipes,
            'arms': arms,
            'paint': paint,
            'base_plate_size': request.POST.get('size'),
            'base_plate_shape': request.POST.get('shape'),
            'base_plate_hole_quantity': request.POST.get('hole_quantity'),
            'base_plate_thickness': request.POST.get('thickness'),
            'jbolt_size': request.POST.get('jsize'),
            'jbolt_thread': request.POST.get('thread'),
            'jbolt_bend': request.POST.get('bend'),
            'status': request.POST.get('status'),
            'arm_bend': request.POST.get('arm_bend'),
            'arm_design': request.POST.get('arm_design'),
            'silver_base': request.POST.get('silver_base'),
            'silver_melon': request.POST.get('silver_melon'),
            'cnc': request.POST.get('cnc'),
            'melon': request.POST.get('melon'),
            'nipple': request.POST.get('nipple'),
            'iron_strips': request.POST.get('iron_strips'),
            'breaker_strips': request.POST.get('breaker_strips'),
            'design': request.POST.get('design'),
            'hinge': request.POST.get('hinge'),
            'holder': request.POST.get('holder'),
        }
        
        form = PoleTransactionForm(data)
        if form.is_valid():
            form.save()
            messages.success(request, "Sale Transaction has been saved.")
            return redirect('pole-page')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    return render(request, 'pole.html')
@login_required
def pole_history(request, pk=None):
    context = {}
    if pk is not None:
        transaction = get_object_or_404(PoleTransaction, pk=pk)
        context['transaction'] = transaction
    context['page_title'] = 'Pole Transaction History'
    return render(request, 'pole-history.html', context)

@login_required
def delete_transaction(request, pk):
    
    if request.method == 'POST':
        transaction = get_object_or_404(PoleTransaction, pk=pk)
        transaction.delete()
        messages.success(request, "Transaction has been deleted.")
      
    return redirect('pole-page')

@login_required
def generate_pdf(request, pk):
    transaction = PoleTransaction.objects.get(pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transaction_{pk}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    font_path = os.path.join(settings.BASE_DIR, 'static/assets/font-awesome/webfonts/Algerian.ttf')
    pdfmetrics.registerFont(TTFont('Algerian', font_path))
    
    # Company Name
    elements.append(Paragraph('<font name="Algerian" color="#f89820">TEKSUN LIGHTS PVT. LTD</font>', styles["Title"]))
    elements.append(Spacer(1, 24))
    
    # Title
    elements.append(Paragraph("Project History", styles["Title"]))
    elements.append(Spacer(1, 12))
    
    # Project Details Table
    project_details_data = [
        ["Customer Name", transaction.customer],
        ["Customer Code", transaction.customer_code],
        ["Project Type", transaction.order_type],
        ["Product Name", transaction.product_name],
        ["Quantity", str(transaction.quantity)],
        ["Status", str(transaction.status)]
    ]
    
    project_details_table = Table(project_details_data, colWidths=[150, 300])
    project_details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    
    elements.append(project_details_table)
    elements.append(Spacer(1, 24))
    
    # Product Used Details Table
    elements.append(Paragraph("Product Used Details", styles["Heading2"]))
    elements.append(Spacer(1, 12))
    
    items_data = [
        ["Item", "Description"],
        ["Pipes", str(transaction.pipes)],
        ["Arms", str(transaction.arms)],
        ["Paint", str(transaction.paint)],
        ["Arm Bend", str(transaction.arm_bend)],
        ["Arm Design", str(transaction.design)],
        ["Silver Melon", str(transaction.silver_melon)],
        ["Silver Base", str(transaction.silver_base)],
        ["CNC", str(transaction.cnc)],
        ["Melon", str(transaction.melon)],
        ["Nipple", str(transaction.nipple)],
        ["Iron Strips", str(transaction.iron_strips)],
        ["Breaker Strips", str(transaction.breaker_strips)],
        ["Design", str(transaction.design)],
        ["Hinge", str(transaction.hinge)],
        ["Holder", str(transaction.holder)],
        ["Base Plate Size", str(transaction.base_plate_size)],
        ["Base Plate Shape", str(transaction.base_plate_shape)],
        ["Base Plate Quantity", str(transaction.base_plate_hole_quantity)],
        ["Base Plate Thickness", str(transaction.base_plate_thickness)],
        ["J-Bolt Size", str(transaction.jbolt_size)],
        ["J-Bolt Thread", str(transaction.jbolt_thread)],
        ["J-Bolt Bend", str(transaction.jbolt_bend)]
    ]
    
    items_table = Table(items_data, colWidths=[150, 300])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
     
    
    elements.append(items_table)
    
    doc.build(elements)
    
    return response


@login_required
def generate_pdf_light(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    invoice_items = Invoice_Item.objects.filter(invoice=invoice)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{pk}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    font_path = os.path.join(settings.BASE_DIR, 'static/assets/font-awesome/webfonts/Algerian.ttf')
    # Register Algerian font
    pdfmetrics.registerFont(TTFont('Algerian', font_path))
    
    # Company Name
    elements.append(Paragraph('<font name="Algerian" color="#f89820" size="20">TEKSUN LIGHTS PVT. LTD</font>', styles["Title"]))
    elements.append(Spacer(1, 24))
    
    # Title
    elements.append(Paragraph("Project History", styles["Title"]))
    elements.append(Spacer(1, 12))
    
    # Project Details Table
    project_details_data = [
        ["Project Code", invoice.transaction],
        ["Customer Name", invoice.customer],
        ["Customer Code", invoice.customer_code],
        ["Project Type", invoice.order_type],
        ["Product Name", invoice.product_name],
        ["Quantity", str(invoice.quantity)],
        ["Total Amount", f"{invoice.total:.2f}"]
    ]
    
    project_details_table = Table(project_details_data, colWidths=[150, 300])
    project_details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(project_details_table)
    elements.append(Spacer(1, 24))
    
    # Product Used Details Table
    elements.append(Paragraph("Products Used", styles["Heading2"]))
    elements.append(Spacer(1, 12))
    
    items_data = [
        ["Product Name", "Quantity", "Price", "Total"]
    ]
    
    for item in invoice_items:
        items_data.append([
            item.product.name,
            str(item.quantity),
            f"{item.price:.2f}",
            f"{float(item.quantity) * float(item.price):.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[200, 100, 100, 100])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(items_table)
    
    doc.build(elements)
    
    return response

@login_required
def generate_inventory_pdf(request):
    products = Product.objects.all()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="inventory.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
  
    
    elements.append(Paragraph('<b>TEKSUN LIGHTS PVT. LTD</b>', styles["Title"]))
    elements.append(Spacer(1, 12))
    
    # Title
    elements.append(Paragraph("Inventory", styles["Title"]))
    elements.append(Spacer(1, 12))
    
    # Inventory Table
    inventory_data = [
        ["Sr.", "Product", "Quantity"]
    ]
    
    for idx, product in enumerate(products, start=1):
        inventory_data.append([
            str(idx),
            product.name,
            str(product.count_inventory())  
        ])
    
    inventory_table = Table(inventory_data, colWidths=[50, 300, 100])
    inventory_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(inventory_table)
    
    doc.build(elements)
    
    return response
@login_required
def sharefile(request):
    context['page_title'] = 'Share File'

    return render(request, 'share-file.html', context)