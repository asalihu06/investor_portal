import requests
from django.conf import settings


def create_payment_page(name, amount_kobo, description, allocation_pk):
  
    url = "https://api.paystack.co/page"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "name": name,
        "amount": amount_kobo,
        "description": description,
        "metadata": {
            "allocation_pk": allocation_pk,
        },
        "collect_phone": True,
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    if data.get("status"):
        page = data["data"]
        page_id = str(page["id"])
        payment_link = f"https://paystack.com/pay/{page['slug']}"
        return page_id, payment_link

    raise ValueError(f"Paystack page creation failed: {data.get('message', 'Unknown error')}")