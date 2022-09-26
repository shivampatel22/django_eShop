from django.shortcuts import render, get_object_or_404, redirect
import braintree
from django.conf import settings
from orders.models import Order
from .tasks import payment_completed

# instatiate the Braintree payment gateway
gateway = braintree.BraintreeGateway(settings.BRAINTREE_CONF)

def payment_process(request):
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id)
    total_cost = order.get_total_cost()

    if request.method == 'POST':
        # retrieve nonce
        nonce = request.POST.get('payment_method_nonce', None)

        # create and submit the transaction
        result = gateway.transaction.sale({
            'amount': f'{total_cost:.2f}',
            'payment_method_nonce': nonce,
            'options':{
                'submit_for_settlement': True
            }
        })
        if result.is_success:
            # mark the order as paid
            order.paid = True
            order.braintree_id = result.transaction.id
            order.save()
            # launch asynchronous task
            payment_completed.delay(order.id)
            return redirect('payment:done')
        else:
            return redirect('payment:canceled', 
                            error_code=result.transaction.processor_response_code, 
                            error_text=result.transaction.processor_response_text)
    else:
        # generate token
        client_token = gateway.client_token.generate()
        return render(request,
                      'payment/process.html',
                      {'order':order,
                       'client_token':client_token})

def payment_done(request):
    return render(request, 'payment/done.html')

def payment_canceled(request, error_code=None, error_text=None):
    return render(request, 'payment/canceled.html', {'error_code':error_code,'error_text':error_text})


