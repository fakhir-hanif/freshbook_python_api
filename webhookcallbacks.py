############# Webhook call backs for registering payment notifications #
########################################################################
import freshbooks
from django.http import HttpResponse
import json
from ItsRelevant.offers.models import FreshbookPayment, Offer, OfferPakage
from datetime import datetime, timedelta

itsr_url = 'acount-url'
itsr_fb_token = 'token'
itsr_unique_ua = 'user agent'


def webhookcallback(request):
    try:
        freshbooks.setup(itsr_url, itsr_fb_token,
                         user_agent_name=itsr_unique_ua)
        call_back_create = freshbooks.call_api('callback.create',
                    {'callback': {'event': 'payment.create',
                        'uri': 'url to handle request'}
                    })
        if call_back_create.success:
            #call_back_id = call_back_create.callback_id
            return HttpResponse(json.dumps({"result": True}))
        return HttpResponse(json.dumps({'result': False}))
    except Exception, e:
        return HttpResponse(json.dumps({'result': str(e)}))


def webhooksNotify(request):
    try:
        name = request.POST.get('name', None)
        object_id = request.POST.get('object_id', None)
        system = request.POST.get('system', None)
        user_id = request.POST.get('user_id', None)
        verifier = request.POST.get('verifier', None)
        freshbooks.setup(itsr_url, itsr_fb_token,
                         user_agent_name=itsr_unique_ua)
        if verifier is None:
            call_back_create = freshbooks.call_api('payment.get',
                                {'payment_id': object_id})
            print "webhooks check", call_back_create
            if call_back_create.success:
                payment_id = object_id
                invoice_id = call_back_create.get_invoice_id
                client_id = call_back_create.get_client_id
                date = call_back_create.get_date
                amount = call_back_create.get_amount
                currency_code = call_back_create.get_currency_code
                payment_type = call_back_create.get_type
                reference_id = call_back_create.get_reference_id
                offer = Offer.objects.get(invoiceId=invoice_id)
                freshbook_payment = FreshbookPayment()
                if None in (amount, date, currency_code, payment_id, offer,
                            client_id, payment_type):
                    raise Exception("All fields are required")
                else:
                    freshbook_payment.amount = amount
                    try:
                        freshbook_payment.paid_on = datetime.strptime(date,
                                                    "%Y-%m-%d %H:%M:%S")
                    except:
                        freshbook_payment.paid_on = datetime.now()
                    freshbook_payment.clientId = client_id
                    freshbook_payment.invoiceId = invoice_id
                    freshbook_payment.offer = offer
                    freshbook_payment.paymentId = payment_id
                    freshbook_payment.currency_code = currency_code
                    freshbook_payment.referenceId = reference_id
                    freshbook_payment.type = payment_type
                    freshbook_payment.save()
                    # Updating offer and setting its Expiry.
                    offer.paid_once = 1
                    if offer.reviewed:
                        offer.status = 1
                    else:
                        offer.status = 5
                    offerpakage = OfferPakage.objects.get(offer=offer,
                                                        invoiceId=invoice_id)
                    offerpakage.status = 1  # status for paid
                    if offerpakage.pakage.id == 1:
                        offer.end_date = datetime.now() + timedelta(days=7)
                        offer.campaign.end_date = datetime.now() +\
                                                        timedelta(days=7)
                    elif offerpakage.pakage.id == 2 or \
                                            offerpakage.pakage.id == 3:
                        offer.end_date = datetime.now() +\
                                                     timedelta(days=31)
                        offer.campaign.end_date = datetime.now() +\
                                                     timedelta(days=31)
                    elif offerpakage.pakage.id == 4:
                        offer.end_date = datetime.now() +\
                                            timedelta(days=2 * 365)
                        offer.campaign.end_date = datetime.now() +\
                                                    timedelta(days=2 * 365)
                    offer.save()
                    offerpakage.save()
                    return HttpResponse(json.dumps({'result': True}))
            else:
                print "There is an error while payment.get"
                return HttpResponse(status=500)
        else:
            call_back_create = freshbooks.call_api('callback.verify',
                                {'callback': {'callback_id': object_id,
                                              'verifier': verifier
                                              }
                                 })
            if call_back_create.success:
                return HttpResponse(json.dumps({'result': True}))
            return HttpResponse(status=500)
    except Exception, e:
        print str(e)
        return HttpResponse(status=500)


def get_invoices(request):
    freshbooks.setup(itsr_url, itsr_fb_token,
                         user_agent_name=itsr_unique_ua)
    call_back_create = freshbooks.call_api('invoice.get',
                        {'invoice_id': 767234})
    if call_back_create.success:
        invoice_id = call_back_create.get_invoice_id
        print call_back_create.get_invoice_id
    return HttpResponse(json.dumps({'invoice': invoice_id}))
