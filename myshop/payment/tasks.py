from celery import shared_task
from orders.models import Order
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import weasyprint
from io import BytesIO

@shared_task
def payment_completed(order_id):
    """
    Task to send an e-mail notification when an order is
    successfully paid.
    """
    order = Order.objects.get(id=order_id)
    # create invoice e-mail
    subject = f'My Shop - Invoice no. {order.id}'
    message = 'Please, find attached the invoice for your recent purchase.'
    email = EmailMessage(subject, 
                         message,
                         'admin@myshop.com',
                         [order.email])
    # generate pdf invoice
    html = render_to_string('orders/order/pdf.html', {'order':order})
    # in memory bytes buffer
    out = BytesIO()
    stylesheets = [weasyprint.css(settings.STATIC_ROOT + 'css/pdf.css')]
    weasyprint.HTML(string=html).write_pdf(out,
                                           stylesheets=stylesheets)
    # attach pdf
    email.attach(f'order_{order.id}.pdf',
                 out.getvalue(),
                 'application/pdf')
    # send email
    email.send()