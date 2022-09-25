import datetime
from django.contrib import admin
from django.urls import reverse
from .models import Order, OrderItem
from django.utils.safestring import mark_safe
from django.http import HttpResponse
import csv

# use inlines to make the dependent model objects editable in parent model admin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

def export_to_csv(modeladmin, request, queryset):
    """
    custom admin action to export orders to csv
    """
    opts = modeladmin.model._meta
    # set content type and dispostion headers to response
    content_disposition = f'attachment; filename={opts.verbose_name}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = content_disposition
    # create writer object by passing response file-like object
    writer = csv.writer(response)
    # get fields of model using model._meta
    fields = [field for field in opts.get_fields() if not \
              field.many_to_many and not field.one_to_many]
    # Write a first row with header information
    writer.writerow([field.verbose_name for field in fields])
    # write data rows
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj, field.name)
            # convert date object into string
            if isinstance(value, datetime.datetime):
                value = value.strftime('%d/%m/%Y')
            data_row.append(value)
        writer.writerow(data_row)
    return response
export_to_csv.short_description = 'Export to CSV'

def order_detail(obj):
    url = reverse('orders:admin_order_detail', args=[obj.id])
    # Django does not allow to return HTML
    return mark_safe(f'<a href="{ url }">View</a>') 

def order_pdf(obj):
    url = reverse('orders:admin_order_pdf', args=[obj.id])
    return mark_safe(f'<a href="{url}">PDF</a>')
order_pdf.short_description = 'Invoice'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'first_name', 'last_name', 'email', 'address', 'postal_code', 'city', 'paid',
        'created', 'updated', order_detail, order_pdf
    ]
    list_filter = ['paid', 'created', 'updated']
    inlines = [OrderItemInline]
    actions = [export_to_csv]

