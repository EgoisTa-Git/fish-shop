import re

import requests
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Filters,
    Updater,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
)

from cms_api import (
    get_all_products,
    get_product,
    get_access_token,
    get_product_available_stock,
    get_file_url_by_id,
    add_product_to_cart,
    get_cart_items,
    remove_cart_item,
    create_customer,
)

HANDLE_MENU, HANDLE_DESCRIPTION, HANDLE_CART, WAITING_EMAIL = range(4)


def start(update, context):
    products = get_all_products(context.bot_data['access_token'])

    keyboard = []
    for product in products:
        keyboard.append(
            [InlineKeyboardButton(product['name'], callback_data=product['id'])]
        )
    keyboard.append(
        [InlineKeyboardButton('Показать корзину', callback_data='show_cart')]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        query = update.callback_query
        context.bot.delete_message(
            query.message.chat_id,
            query.message.message_id,
        )
    except AttributeError:
        pass

    message = context.bot.send_message(
        text='Пожалуйста выберите товар:',
        chat_id=update.effective_chat.id,
    )
    context.bot.edit_message_reply_markup(
        chat_id=message.chat_id,
        message_id=message.message_id,
        reply_markup=reply_markup,
    )
    return HANDLE_MENU


def handle_menu(update, context):
    query = update.callback_query

    product = get_product(context.bot_data['access_token'], query.data)
    product_price = product['meta']['display_price']['with_tax']['formatted']
    product_name = product['attributes']['name']
    product_description = product['attributes']['description']
    product_image_id = product['relationships']['main_image']['data']['id']
    product_image_url = get_file_url_by_id(
        context.bot_data['access_token'],
        product_image_id,
    )
    available_stock = get_product_available_stock(
        context.bot_data['access_token'],
        query.data,
    )

    response = requests.get(product_image_url)
    response.raise_for_status()
    product_image = response.content

    text = f"Выбран товар: {product_name} \
    \n{product_price} per kg \n{product_description} \
    \n{available_stock} in stock available"

    context.bot.delete_message(query.message.chat_id, query.message.message_id)

    context.user_data['selected_product'] = query.data
    message = context.bot.send_photo(
        query.message.chat_id,
        product_image,
        caption=text
    )

    keyboard = [
        [InlineKeyboardButton('Добавить в корзину 5 кг', callback_data='5')],
        [InlineKeyboardButton('Добавить в корзину 10 кг', callback_data='10')],
        [InlineKeyboardButton('Добавить в корзину 15 кг', callback_data='15')],
        [InlineKeyboardButton('Показать корзину', callback_data='show_cart')],
        [InlineKeyboardButton('Назад', callback_data='menu')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=message.message_id,
        reply_markup=reply_markup,
    )
    return HANDLE_DESCRIPTION


def show_cart(update, context):
    query = update.callback_query
    cart = get_cart_items(
        context.bot_data['access_token'],
        query.message.chat_id,
    )

    context.bot.delete_message(query.message.chat_id, query.message.message_id)

    text = 'Сейчас в корзине:\n'

    keyboard = []
    for product in cart['data']:
        text += f'\n{product["name"]}'
        text += f'\n{product["description"]}'
        unit_price = product['unit_price']['amount'] / 100
        text += f'\n${unit_price:.2f} per kg'
        price = product['value']['amount'] / 100
        quantity = product['quantity']
        text += f'\n{quantity}kg in cart for ${price:.2f}\n'
        keyboard.append(
            [
                InlineKeyboardButton(
                    f'Убрать из корзины {product["name"]}',
                    callback_data=product['id'],
                ),
            ]
        )

    total_price = cart['meta']['display_price']['with_tax']['formatted']
    text += f'\nTotal: {total_price}'

    message = context.bot.send_message(
        text=text,
        chat_id=update.effective_chat.id,
    )

    keyboard.append([InlineKeyboardButton('В меню', callback_data='menu')])
    keyboard.append([InlineKeyboardButton('Оплата', callback_data='mail')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=message.message_id,
        reply_markup=reply_markup,
    )
    return HANDLE_CART


def add_item_to_cart(update, context):
    query = update.callback_query
    quantity = int(query.data)
    add_product_to_cart(
        context.bot_data['access_token'],
        query.message.chat_id,
        context.user_data['selected_product'],
        quantity,
    )
    return HANDLE_DESCRIPTION


def remove_item_from_cart(update, context):
    query = update.callback_query
    remove_cart_item(
        context.bot_data['access_token'],
        query.message.chat_id,
        query.data,
    )
    show_cart(update, context)
    return HANDLE_CART


def get_user_mail(update, context):
    query = update.callback_query
    context.bot.send_message(
        text='Пожалуйста пришлите Ваш email',
        chat_id=query.message.chat_id,
    )
    return WAITING_EMAIL


def checkout(update, context):
    if re.match(r'[^@]+@[^@]+\.[^@]+', update.message.text):
        update.message.reply_text(
            f'E-mail {update.message.text} проверен. Заказ оформлен.'
        )
        create_customer(
            context.bot_data['access_token'],
            update.effective_user.name,
            update.message.text,
        )
        return ConversationHandler.END
    else:
        context.bot.send_message(
            text='Уточните, пожалуйста, Ваш email',
            chat_id=update.message.chat_id,
        )
        return WAITING_EMAIL


def cancel(update, context):
    update.message.reply_text('До новых встреч!')
    return ConversationHandler.END


def renew_access_token(context):
    client = context.bot_data['client_id']
    secret = context.bot_data['client_secret']
    token = get_access_token(client, secret)
    context.bot_data['access_token'] = token


if __name__ == '__main__':
    env = Env()
    env.read_env()
    tg_token = env('TELEGRAM_TOKEN')
    client_id = env('CLIENT_ID')
    client_secret = env('CLIENT_SECRET')

    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    access_token = get_access_token(client_id, client_secret)
    dispatcher.bot_data['client_id'] = client_id
    dispatcher.bot_data['client_secret'] = client_secret
    dispatcher.bot_data['access_token'] = access_token

    job_queue = updater.job_queue
    job_queue.run_repeating(renew_access_token, interval=3600, first=0)

    states = {
        HANDLE_MENU: [
            CallbackQueryHandler(show_cart, pattern='show_cart'),
            CallbackQueryHandler(handle_menu),
        ],
        HANDLE_DESCRIPTION: [
            CallbackQueryHandler(show_cart, pattern='show_cart'),
            CallbackQueryHandler(start, pattern='menu'),
            CallbackQueryHandler(add_item_to_cart),
        ],
        HANDLE_CART: [
            CallbackQueryHandler(start, pattern='menu'),
            CallbackQueryHandler(get_user_mail, pattern='mail'),
            CallbackQueryHandler(remove_item_from_cart),
        ],
        WAITING_EMAIL: [
            MessageHandler(Filters.text, checkout),
        ],
    }

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states=states,
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()
