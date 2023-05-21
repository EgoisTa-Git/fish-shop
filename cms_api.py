import requests


def get_access_token(client, secret):
    access_url = 'https://api.moltin.com/oauth/access_token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    payload = {
        'client_id': client,
        'client_secret': secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post(access_url, headers=headers, data=payload)
    response.raise_for_status()
    return response.json()['access_token']


def get_all_products(token):
    products_url = 'https://api.moltin.com/pcm/products'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(products_url, headers=headers)
    response.raise_for_status()
    items = []
    for item in response.json()['data']:
        item['attributes']['id'] = item['id']
        items.append(item['attributes'])
    return items


def get_product(token, product_id):
    product_url = f'https://api.moltin.com/catalog/products/{product_id}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(product_url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def add_product_to_cart(token, cart_id, product_id, quantity):
    cart_url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity,
        }
    }
    response = requests.post(cart_url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def get_cart_items(token, cart_id):
    cart_url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(cart_url, headers=headers)
    response.raise_for_status()
    return response.json()


def remove_cart_item(token, cart_id, product_id):
    item_url = f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.delete(item_url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_product_available_stock(token, product_id):
    stock_url = f'https://api.moltin.com/v2/inventories/{product_id}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(stock_url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['available']


def get_file_url_by_id(token, file_id):
    file_url = f'https://api.moltin.com/v2/files/{file_id}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(file_url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['link']['href']


def create_customer(token, name, email):
    customer_url = 'https://api.moltin.com/v2/customers'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'data': {
            'type': 'customer',
            'name': name,
            'email': email,
        }
    }
    response = requests.post(customer_url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
