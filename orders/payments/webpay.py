from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_type import IntegrationType
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys

from django.conf import settings
from django.urls import reverse
from django.db import transaction


from orders.models import Order


def get_return_url():
    return settings.BACKEND_URL + reverse("webpay-return")


tx = Transaction(
    WebpayOptions(
        IntegrationCommerceCodes.WEBPAY_PLUS,
        IntegrationApiKeys.WEBPAY,
        IntegrationType.TEST,
    )
)


def create_webpay_transaction(order: Order):
    if order.status != Order.Status.PENDING:
        raise ValueError("Solo se puede pagar una orden pendiente")

    response = tx.create(
        buy_order=order.order_number,
        session_id=str(order.pk),
        amount=int(order.total.amount),
        return_url=get_return_url(),
    )

    order.payment_reference = response["token"]
    order.save(update_fields=["stripe_payment_intent_token"])

    return response


@transaction.atomic
def handle_webpay_return(token: str):
    response = tx.commit(token)

    order = Order.objects.select_for_update().get(payment_reference=token)

    if response["status"] == "AUTHORIZED" and response["response_code"] == 0:
        order.confirm()
    else:
        order.cancel()

    return (response, order)
