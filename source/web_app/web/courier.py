from flask import template_rendered


def logo():
    with open(r'web\static\image\logo.png', 'rb') as file:
        data = file.read()
    return data


def html_courier(telegram_id):
    with open(r'web\templates\courier.html', 'rb') as file:
        data = file.read()
    return data
    # return template_rendered(r"courier.html", catalogs=r"web\templates")


def js_courier():
    with open(r'web\static\js\courier.js', 'r') as file:
        data = file.read()
    return data


def css_courier():
    with open(r'web\static\css\courier2.css', 'rb') as file:
        data = file.read()
    return data
