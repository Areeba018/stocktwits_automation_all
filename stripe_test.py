import os
import stripe

from dotenv import load_dotenv

load_dotenv(verbose=True)
stripe.api_key = os.getenv('STRIPE_API_KEY')


def create_customer():
    customer_data = {
        "email": "jane.doe@example.com",
        "name": "Jane Doe",
        "address": {
            "line1": "123 Main St",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94111",
            "country": "US"
        }
    }

    customer = stripe.Customer.create(**customer_data)
    print(customer.id)


def create_payment_method():
    payment_method_data = {
        "type": "card",
        "card": {
            "number": "4242424242424242",
            "exp_month": 12,
            "exp_year": 2025,
            "cvc": "123"
        }
    }
    payment_method = stripe.PaymentMethod.create(**payment_method_data)
    print(payment_method.id)


def attach_payment_method():

    customer_id = 'cus_NiHweiDOy7mykE'
    payment_method_id = 'pm_1MwrTeK5q3eJWauvYwVMVxk1'

    stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)

