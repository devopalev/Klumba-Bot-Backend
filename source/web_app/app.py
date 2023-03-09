import logging
from flask import Flask, request
from flask_restful import Api
from source.web_app.rest.v1 import event
from source.web_app.rest.v1.approve import Approve
from source.web_app.api_socket import BotConnector
from source import secret
from source.web_app.web import courier as web_courier
from source.web_app.rest.v1 import courier as rest_courier

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
api = Api(app)


@app.before_request
def authorization():
    token_arg = request.args.get("token")
    #TODO: срабатывает на запрос иконки, скриптов и тд
    # if token_arg not in creds.WEB_TOKENS:
    #     return '{"error": "bad token"}', 403  # Forbidden


@app.route('/testing')
def get():
    result = BotConnector.build().send({"action": "testing"}, wait_answer=True)
    return {"result": result}, 200


# WEB APP TELEGRAM
app.add_url_rule('/webapp/logo.png', view_func=web_courier.logo)
app.add_url_rule(secret.WEB_COURIER_URL + '/<telegram_id>', view_func=web_courier.html_courier)
app.add_url_rule('/webapp/courier.js', view_func=web_courier.js_courier)
app.add_url_rule('/webapp/courier.css', view_func=web_courier.css_courier)


# REST API
api.add_resource(Approve, '/api/v1/approve')
api.add_resource(rest_courier.DealsToday, '/api/v1/courier/deals_today')
api.add_resource(rest_courier.DealsTomorrow, '/api/v1/courier/deals_tomorrow')
api.add_resource(rest_courier.DealsEarly, '/api/v1/courier/deals_early')
api.add_resource(rest_courier.DoneDeal, '/api/v1/courier/deal/done')
api.add_resource(rest_courier.ReturnDeal, '/api/v1/courier/deal/return')
api.add_resource(event.EventUser, '/api/v1/event/user')
api.add_resource(event.EventEquip, '/api/v1/event/equip')
api.add_resource(event.EventReserve, '/api/v1/event/reverse')
api.add_resource(event.EventUnapproved, '/api/v1/event/unapproved')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=30300, debug=False, ssl_context=("msopalev.crt", 'msopalev.key'))
