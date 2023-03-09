# -*- coding: utf-8 -*-
import json

from flask_restful import Resource, reqparse
from source.web_app.api_socket import BotConnector


class DealsToday(Resource):
    bot = BotConnector.build()
    parser = reqparse.RequestParser()
    parser.add_argument("telegram_id", location='args', help="ID telegram user")
    parser.add_argument("token", location='args', help="TOKEN authorization")

    def get(self):
        args = self.parser.parse_args()
        result = self.bot.send({"action": "courier_deals_today", "telegram_id": args.telegram_id}, wait_answer=True)

        res = {'result': [{'ID': '183923',
                'text': '№ заказа: 183923\nВремя: 17:00-19:00\nДата: 2022-10-02\nАдрес: тула\nКвартира: 12\nИмя получателя: None\nТелефон получателя: None\nРайон: Проспект справа\nКомментарий по доставке: 123\n\nИнкогнито: нет\n\nК оплате: 2\nПодразделение: Стадион\nКто отправил заказ: Опалев Максим\nТелефон заказчика (если получатель не отвечает): 89964316090'},
               {'ID': '183924', 'text': 'тестовый блок 1'}, {'ID': '183925', 'text': 'тестовый блок 2'}]}
        return res, 200


class DealsTomorrow(Resource):
    bot = BotConnector.build()
    parser = reqparse.RequestParser()
    parser.add_argument("telegram_id", location='args', help="ID telegram user")
    parser.add_argument("token", location='args', help="TOKEN authorization")

    def get(self):
        args = self.parser.parse_args()
        result = self.bot.send({"action": "courier_deals_tomorrow", "telegram_id": args.telegram_id}, wait_answer=True)
        return result, 200


class DealsEarly(Resource):
    bot = BotConnector.build()
    parser = reqparse.RequestParser()
    parser.add_argument("telegram_id", location='args', help="ID telegram user")
    parser.add_argument("token", location='args', help="TOKEN authorization")

    def get(self):
        args = self.parser.parse_args()
        result = self.bot.send({"action": "courier_deals_early", "telegram_id": args.telegram_id}, wait_answer=True)
        return result, 200


class DoneDeal(Resource):
    bot = BotConnector.build()
    parser = reqparse.RequestParser()
    parser.add_argument("telegram_id", location='args', help="ID telegram user")
    parser.add_argument("deal_id", location='args', help="ID deal")
    parser.add_argument("token", location='args', help="TOKEN authorization")

    def post(self):
        args = self.parser.parse_args()
        result = self.bot.send({"action": "courier_deal_done", "telegram_id": args.telegram_id,
                                "deal_id": args.deal_id}, wait_answer=True)
        return result, 200


class ReturnDeal(Resource):
    bot = BotConnector.build()
    parser = reqparse.RequestParser()
    parser.add_argument("telegram_id", location='args', help="ID telegram user")
    parser.add_argument("deal_id", location='args', help="ID deal")
    parser.add_argument("token", location='args', help="TOKEN authorization")

    def post(self):
        args = self.parser.parse_args()
        result = self.bot.send({"action": "courier_deal_return", "telegram_id": args.telegram_id,
                                "deal_id": args.deal_id}, wait_answer=True)
        return result, 200
