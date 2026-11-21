from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from celery.result import AsyncResult
from .models import Product
from .serializers import ProductSerializer
from .tasks import process_product


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def list(self, request, *args, **kwargs):
        cache_key = "products_list"
        data = cache.get(cache_key)

        if not data:
            serializer = self.get_serializer(self.get_queryset(), many=True)
            data = serializer.data
            cache.set(cache_key, data, 60)

        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        cache_key = f"product_{pk}"
        data = cache.get(cache_key)

        if not data:
            product = self.get_object()
            data = ProductSerializer(product).data
            cache.set(cache_key, data, 60)

        return Response(data)

    def perform_create(self, serializer):
        product = serializer.save()
        cache.clear()
        task = process_product.delay(product.id)
        self.task_id = task.id

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs) 
        response.data['task_id'] = getattr(self,'task_id',None)
        return response
    

    def perform_update(self, serializer):
        serializer.save()
        cache.clear()

    def perform_destroy(self, instance):
        instance.delete()
        cache.clear()

@api_view(['GET'])
def task_status(request,task_id):
    result = AsyncResult(task_id)
    return Response({
        'task_id':task_id,
        'status':result.status,
        'result':result.result if result.ready() else None,
    })
