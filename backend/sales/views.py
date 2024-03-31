from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from collections import defaultdict
from sales.models import Sales
from stocks.models import Stock
from company.models import Company
from sales.serializers import SalesAddSerializers

class SalesAddView(APIView):
    def post(self, request):
        serializer = SalesAddSerializers(data=request.data)
        if serializer.is_valid():
            sale_data = serializer.validated_data
            try:
                stock_item = get_object_or_404(Stock, items_name=sale_data["items_name"])
                if stock_item.quantity < sale_data["quantity"]:
                    raise ValidationError("Not enough stock available.")
                stock_item.quantity -= sale_data["quantity"]
                stock_item.save()
                serializer.save()
                message = f"Sale of {sale_data['quantity']} {sale_data['items_name']} made successfully."
                return Response({"detail": message}, status=status.HTTP_201_CREATED)
            except (Stock.DoesNotExist, ValidationError) as e:
                return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  
class SalesStatsAPIView(APIView):
    def get(self, request):
        num_of_sells = Sales.num_of_sells()
        stats = {
            "num_of_sells": num_of_sells,
            "total_sales_amount": Sales.total_sales_amount(),
            "total_receivable_amt": Sales.total_receivable_amt(),
            "total_tax_amount": Sales.total_tax_amount(),
        }
        return Response(stats, status=status.HTTP_200_OK)

class SalesListView(ListAPIView):
    queryset = Sales.objects.all()
    serializer_class = SalesAddSerializers

class ItemsSoldCounterView(APIView):
    def get(self, request):
        items_sold = self.count_items_sold()
        self.check_popular_items(items_sold)
        return Response(items_sold, status=status.HTTP_200_OK)

    def count_items_sold(self):
        sales_data = Sales.objects.all()
        items_sold = defaultdict(int)
        for sale in sales_data:
            items_sold[sale.items_name] += 1
        return dict(items_sold)

    def send_popular_item_email(self, item_name):
        company_name = Company.objects.first().name  
        subject = f"🔥 Limited Stock Alert from {company_name}! 🔥"
        message = f"""
Attention Shoppers! 🛍

At {company_name}, our popular item "{item_name}" is flying off the shelves! 🚀 Don't miss out on this hot deal! 🔥

Act now before we run out of stock! Hurry and secure your favorite item before someone else does. 💨

Shop now at {company_name} and enjoy exclusive savings on "{item_name}" today! 💰

Happy Shopping!
"""
        sender_email = settings.DEFAULT_FROM_EMAIL
        recipient_email = ['sajanluitel123@gmail.com', 'kastisuhesh1@gmail.com', 'shakeshrestha@gmail.com']
        send_mail(subject, message, sender_email, recipient_email, fail_silently=False)

    def check_popular_items(self, items_sold):
        for item_name, num_sold in items_sold.items():
            if num_sold > 3:
                self.send_popular_item_email(item_name)
