from flask_restful import Resource, reqparse
from source.web_app.api_socket import BotConnector
from source.web_app.Tasks import Task, TaskEventUser


class EventUser(Resource):
    bot = BotConnector.build()

    parser = reqparse.RequestParser()
    parser.add_argument("bitrix_id", location='args', help="ID bitrix user")
    parser.add_argument("text", location='args', help="Text message")
    parser.add_argument("token", location='args', help="TOKEN authorization")

    def post(self):
        args = self.parser.parse_args()

        self.bot.send(TaskEventUser(args.bitrix_id, args.text))
        return {"result": "ok"}, 200


class EventEquip(Resource):
    bot = BotConnector.build()

    parser = reqparse.RequestParser()
    parser.add_argument("deal_id", location='args', help="ID bitrix user")
    parser.add_argument("token", location='args', help="TOKEN authorization")

    def post(self):
        args = self.parser.parse_args()
        self.bot._queue_recv.put({"action": "event_equip", "deal_id": args.deal_id})
        return {"result": "ok"}, 200


class EventReserve(Resource):
    bot = BotConnector.build()

    parser = reqparse.RequestParser()
    parser.add_argument("deal_id", location='args', help="ID bitrix user")
    parser.add_argument("token", location='args', help="TOKEN authorization")

    def post(self):
        args = self.parser.parse_args()
        self.bot._queue_recv.put({"action": "event_reserve", "deal_id": args.deal_id})
        return {"result": "ok"}, 200


class EventUnapproved(Resource):
    bot = BotConnector.build()

    parser = reqparse.RequestParser()
    parser.add_argument("deal_id", location='args', help="ID bitrix user")
    parser.add_argument("token", location='args', help="TOKEN authorization")

    def post(self):
        args = self.parser.parse_args()
        self.bot._queue_recv.put({"action": "event_unapproved", "deal_id": args.deal_id})
        return {"result": "ok"}, 200