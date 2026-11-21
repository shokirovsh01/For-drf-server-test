import time 
from celery import shared_task
from .models import Product
from django.core.cache import cache

@shared_task
def process_product(product_id):
    time.sleep(10)
    Product.objects.filter(id=product_id).update(is_processed=True)
    cache.clear()
    return f'Product {product_id} processed'

@shared_task
def count_products():
    total = Product.objects.count()
    print(f'Total count in db {total}')
    return total
