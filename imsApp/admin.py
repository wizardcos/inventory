from django.contrib import admin
from imsApp.models import Category, Product, Stock,PoleTransaction, Invoice, Invoice_Item

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Stock)
admin.site.register(Invoice)
admin.site.register(Invoice_Item)
admin.site.register(PoleTransaction)