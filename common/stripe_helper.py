import os
import stripe
import stripe.error
import traceback

from dotenv import load_dotenv
from common.exceptions import GeneralException

load_dotenv(verbose=True)

# Set your Stripe API key
stripe.api_key = os.getenv('STRIPE_API_KEY', '')


class Response:
    def __init__(self):
        pass


def validate_payment_method(payment_method_id):
    pm = stripe.PaymentMethod.retrieve(payment_method_id)

    return pm


def add_payment_method_to_customer(payment_method_id, customer_id):
    pm = stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)

    return pm












def tokenize_card(card):
    try:
        token = stripe.Token.create(
            card= card,
        )
        return token
    except stripe.error.CardError as e:
        # Handle errors
        traceback.print_exc()
        pass


def verify_payment_method(payment_method):

    print("payment method verification")
    resp = charge_amount('Verification', dollars=1.0, payment_method=payment_method)
    if resp.status == "succeeded":
        card = resp['payment_method_details']['card']
        print(f'Brand: {card["brand"]} Country: {card["country"]} ')
        resp = refund_charge(resp['id'])
        return card["brand"], card["country"]

    return None, None


def charge_amount(description, dollars, payment_method):
    # Create a Stripe charge with credit card details
    cents = int(round(dollars * 100, 2))

    month, year = payment_method['card_expiry'].split('/')

    card = {
        'number': payment_method['card_number'],
        'exp_month': month,
        'exp_year': year,
        'cvc': payment_method['card_cvc'],
    }

    tok_visa = tokenize_card(card)

    print('~' * 100)
    print(tok_visa)
    print('~' * 100)

    try:
        charge = stripe.Charge.create(
            amount=cents,  # amount in cents
            currency="usd",
            description=description,
            source=tok_visa
        )

        # Handle the response from Stripe
        # if charge.status == "succeeded":
        #     print("Charge successful")
        # else:
        #     print("Charge failed")

        return charge

    except stripe.error.CardError as e:
        # Handle errors
        print(e.code, e.http_status, e.error, e.user_message)
        resp = Response()
        setattr(resp, 'code', e.http_status)
        setattr(resp, 'status', 'error')
        setattr(resp, 'reason', e.code)
        setattr(resp, 'message', e.user_message)
        return resp


def refund_charge(charge_id, amount=None):
    try:
        refund = stripe.Refund.create(
            charge=charge_id,
            amount=amount
        )

        # Handle the response from Stripe
        # if refund.status == "succeeded":
        #     print("Refund successful")
        # else:
        #     print("Refund failed")

        return refund

    except stripe.error.CardError as e:
        print(e.code, e.http_status, e.error, e.user_message)
        # Handle errors
        resp = Response()
        setattr(resp, 'code', e.http_status)
        setattr(resp, 'status', 'error')
        setattr(resp, 'reason', e.code)
        setattr(resp, 'message', e.user_message)
        return resp


def charge_subscription(description, dollars, customer_id, method_id):

    cents = int(round(dollars * 100, 2))

    try:
        intent = stripe.PaymentIntent.create(
            description=description,
            amount=cents,
            currency='usd',
            customer=customer_id,
            payment_method=method_id,
            confirm=True,
            return_url='http://localhost:8091/',
            automatic_payment_methods={"enabled": True},
        )
        return intent

    except stripe.error.CardError as e:
        # Handle errors
        print(e.code, e.http_status, e.error, e.user_message)
        resp = Response()
        setattr(resp, 'code', e.http_status)
        setattr(resp, 'status', 'error')
        setattr(resp, 'reason', e.code)
        setattr(resp, 'message', e.user_message)
        return resp

    except Exception as e:
        print(f'{e}')
        resp = Response()
        setattr(resp, 'code', '400')
        setattr(resp, 'status', 'error')
        setattr(resp, 'reason', 'Unknown')
        setattr(resp, 'message', 'Unknown')
        return resp


def create_stripe_customer(name, email):
    customer_data = {
        "name": name,
        "email": email,
    }

    customer = stripe.Customer.create(**customer_data)
    if (customer):
        return customer.id
    else:
        raise GeneralException(500, 'Could not register user with stripe')



def add_stripe_card_payment_method(data, customer_id):
    exp_month = data['expiry_month'].split('/')[0]
    exp_year = data['expiry_month'].split('/')[1]

    payment_method_data = {
        "type": "card",
        "card": {
            "number": data['card_number'],
            "exp_month": exp_month,
            "exp_year": exp_year,
            "cvc": data['card_cvc']
        }
    }
    payment_method = stripe.PaymentMethod.create(**payment_method_data)

    stripe.PaymentMethod.attach(payment_method.id, customer=customer_id)

    return payment_method.id


def delete_payment_method(payment_method_id):
    try:
        payment_method = stripe.PaymentMethod.detach(payment_method_id)
        return payment_method
    except stripe.error.CardError as e:
        print(e.code, e.http_status, e.error, e.user_message)
        # Handle errors
        pass


def main():

    payment_method = {
        'card_number': '4000000000000127',
        'card_expiry': '12/2025',
        'card_cvc': '123'
    }

    # brand, country = verify_payment_method(payment_method)
    # if brand is None:
    #     print("invalid card details")
    #     return
    #
    # print(f'Brand: {brand} Country: {country}')

    print("service charges")
    resp = charge_amount("Some Service", dollars=0, payment_method=payment_method)
    if resp.status == "error":
        print(resp.code, resp.reason, resp.message)

    if resp.status == "succeeded":
        print(resp['id'], resp['receipt_url'])


if __name__ == "__main__":

    main()


# # Create a PaymentIntent with the payment information
# payment_intent = stripe.PaymentIntent.create(
#     amount=100, # amount in cents
#     currency="usd",
#     payment_method_types=["card"],
# )

# # Get the customer ID from the PaymentIntent object
# customer_id = payment_intent.customer

# customer = stripe.Customer.retrieve(customer_id)
# print(customer.email)





# # Create a Stripe charge with credit card details
# charge = stripe.Charge.create(
#     amount= 1000, # amount in cents
#     currency="usd",
#     description="Example charge",
#     source="tok_visa"
#     # source={
#     #     "object": "card",
#     #     "number": "4242424242424242", # replace with a valid credit card number
#     #     "exp_month": 12,
#     #     "exp_year": 2024,
#     #     "cvc": "123"
#     # }
# )

# # customer_id = "cus_1234567890" # replace with a valid customer ID
# cards = stripe.Customer.list_sources(
#   customer_id,
#   object='card'
# )

# # Print the card details
# for card in cards.data:
#   print("Brand:", card.brand)
#   print("Country:", card.country)
#   print("Last 4 digits:", card.last4)

# # Handle the response from Stripe
# # if charge.status == "succeeded":
# #     print("Charge successful")
# # else:
# #     print("Charge failed")
