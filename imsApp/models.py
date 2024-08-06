from re import I
from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from more_itertools import quantify
from django.db.models import Sum
from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField()
    status = models.CharField(max_length=2, choices=(('1', 'Active'), ('2', 'Inactive')), default='1')
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    code = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=250, blank=True, null=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    model = models.CharField(max_length=250, blank=True, null=True)
    watt = models.CharField(max_length=250, blank=True, null=True)
    volt = models.CharField(max_length=250, blank=True, null=True)
    size = models.CharField(max_length=250, blank=True, null=True)
    length = models.CharField(max_length=250, blank=True, null=True)
    price = models.FloatField(default=0)
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code + ' - ' + self.name


    def count_inventory(self):
        stocks = Stock.objects.filter(product = self)
        stockIn = 0
        stockOut = 0
        for stock in stocks:
            if stock.type == '1':
                stockIn = int(stockIn) + int(stock.quantity)
            else:
                stockOut = int(stockOut) + int(stock.quantity)
        available  = stockIn - stockOut
        return available

class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0)
    type = models.CharField(max_length=2,choices=(('1','Stock-in'),('2','Stock-Out')), default = 1)
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.code + ' - ' + self.product.name

     
        
class Invoice(models.Model):
    transaction = models.CharField(max_length=250)
    customer = models.CharField(max_length=250)
    customer_code= models.CharField(max_length=100)
    order_type =  models.CharField(
    max_length=250,
    choices=[
        ('conventional_light', 'Conventional Light'),
        ('solar_light', 'Solar Light'),
        ('wall_washer', 'Wall Washer'),
        ('flood_light', 'Flood Light'),
        ('fancy_lights', 'Fancy Lights')
    ]
)  
    product_name = models.CharField(max_length=250, blank=True, null=True)
    quantity = models.CharField(max_length=100)   # added field
    description = models.TextField(max_length=500, null=True, blank=True)
    total = models.FloatField(default=0)
    status = models.CharField(max_length=2, choices=(('1', 'Active'), ('2', 'Completed'), ('3', 'Inactive')), default='1')
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.customer

    def item_count(self):
        return Invoice_Item.objects.filter(invoice=self).aggregate(Sum('quantity'))['quantity__sum']

class Invoice_Item(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, blank= True, null= True)
    price = models.FloatField(default=0)
    quantity = models.CharField(max_length=100)

    def __str__(self):
       return f"{self.product.name} ({self.quantity})"




@receiver(models.signals.post_save, sender=Invoice_Item)
def stock_update(sender, instance, **kwargs):
    stock = Stock(product = instance.product, quantity = instance.quantity, type = 2)
    stock.save()
    
    Invoice_Item.objects.filter(id= instance.id).update(stock=stock)

@receiver(models.signals.post_delete, sender=Invoice_Item)
def delete_stock(sender, instance, **kwargs):
    try:
        stock = Stock.objects.get(id=instance.stock.id).delete()
    except:
        return instance.stock.id

class PoleTransaction(models.Model):
    
    customer = models.CharField(max_length=255)
    customer_code = models.CharField(max_length=100)
    order_type =  models.CharField(
    max_length=250,
    choices=[
        ('street_light_pole', 'Street Light Pole'),
        ('fancy_street_pole', 'Fancy Street Pole'),
        ('simple_paint_pole', 'Simple Paint Pole'),
        ('dynamic_Pole', 'Dynamic Pole'),
        
    ]
)  
    product_name = models.CharField(max_length=255)
    quantity = models.CharField(max_length=100)
    description = models.TextField(max_length=500, null=True, blank=True)
    pipes = models.JSONField(default=list)  
    arms = models.JSONField(default=list)   
    base_plate_size = models.CharField(max_length=255, null=True, blank=True)
    base_plate_shape = models.CharField(max_length=255, null=True, blank=True)
    base_plate_hole_quantity = models.CharField(max_length=255, null=True, blank=True)
    base_plate_thickness = models.CharField(max_length=255, null=True, blank=True)
    jbolt_size = models.CharField(max_length=255, null=True, blank=True)
    jbolt_thread = models.CharField(max_length=255, null=True, blank=True)
    jbolt_bend = models.CharField(max_length=255, null=True, blank=True)
    ## new entries strt from here 
    arm_bend = models.CharField(max_length=255, null=True, blank=True)
    arm_design = models.CharField(max_length=255, null=True, blank=True)
    silver_base = models.CharField(max_length=255, null=True, blank=True)
    silver_melon = models.CharField(max_length=255, null=True, blank=True)
    cnc = models.CharField(max_length=255, null=True, blank=True)
    melon = models.CharField(max_length=255, null=True, blank=True)
    nipple = models.CharField(max_length=255, null=True, blank=True)
    iron_strips = models.CharField(max_length=255, null=True, blank=True)
    breaker_strips = models.CharField(max_length=255, null=True, blank=True)
    design = models.CharField(max_length=255, null=True, blank=True)
    hinge = models.CharField(max_length=255, null=True, blank=True)
    holder = models.CharField(max_length=255, null=True, blank=True)
    ## for paint 
    paint =  models.JSONField(default=list)  
    ## new entries end here 
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255, choices=[('1', 'Active'), ('2', 'Completed'), ('3', 'Inactive')], default='1')
     
    def __str__(self):
        return self.customer