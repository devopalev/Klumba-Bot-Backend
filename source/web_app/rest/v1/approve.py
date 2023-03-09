from flask_restful import Resource, reqparse
from source.web_app.api_socket import BotConnector


class Approve(Resource):
    bot = BotConnector.build()

    parser = reqparse.RequestParser()
    parser.add_argument("deal_id", location='args', help="ID deal")
    parser.add_argument("token", location='args', help="TOKEN authorization")

    def post(self):
        args = self.parser.parse_args()
        BotConnector().queue.put({"action": "approve", "deal_id": args.deal_id})
        return {"result": "ok"}, 200
