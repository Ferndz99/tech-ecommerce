from django.conf import settings

from django.core.mail import send_mail

def send_order_confirmation_email(order):

    track_url = f"{settings.BACKEND_URL}/api/v1/orders/track/{order.access_token}/"

    send_mail(
        subject="Confirmación de tu orden",
        message=f"Puedes ver tu orden aquí:\n{track_url}",
        recipient_list=[order.customer_email],
        from_email=settings.DEFAULT_FROM_EMAIL,
    )