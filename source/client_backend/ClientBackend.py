import logging
import sys
import os
from flask import Flask, request, jsonify, Response

# include top level project directory to reuse modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

import source.config as cfg

import StorageHandlers as StorageHandlers
import BitrixHandlers

app = Flask(__name__)
APP_PORT = 8083

# journalctl logging when running via systemctl
logging.basicConfig(level=cfg.LOG_LEVEL, format=cfg.LOG_FORMAT)
logger = logging.getLogger(__name__)


@app.route('/')
def hello():
    return 'Hello!'


@app.route('/<string:digest>', methods=['GET'])
def get_deal_info(digest):
    try:
        logger.info('New get deal info request: %s', digest)

        deal_id = StorageHandlers.get_deal_id(digest)

        if not deal_id:
            return Response('Заказ не найден', status=404)

        deal_desc = BitrixHandlers.get_deal_info_for_client(deal_id)

        if not deal_desc:
            return Response("Ошибка при получении данных заказа", status=503)

        deal_desc.photos = StorageHandlers.get_deal_photos_path(digest)
        rsp = vars(deal_desc)
        rsp['id'] = deal_id

        return jsonify(rsp)
    except Exception as e:
        logger.error('Get deal request error: %s', e)
        return Response('Внутренняя ошибка сервера', status=500)


@app.route('/<string:digest>', methods=['POST'])
def update_deal(digest):
    try:
        logger.info('New update deal info request: %s', digest)

        deal_id = StorageHandlers.get_deal_id(digest)

        if not deal_id:
            return Response('Заказ не найден', status=404)

        stage_check_result = BitrixHandlers.check_deal_stage_before_update(deal_id)

        if stage_check_result is None:
            return Response('Внутренняя ошибка при обновлении заказа', status=503)

        if not stage_check_result:
            return Response('Заказ уже был согласован', status=501)

        if request.is_json:
            data = request.json
        else:
            return Response('Данные клиента должны быть переданы в виде json', status=400)

        logger.info('Request body json data: %s', data)

        result = BitrixHandlers.update_deal_by_client(deal_id, data)

        if not result:
            return Response('Внутренняя ошибка при обновлении заказа', status=503)

        return Response('Заказ успешно обновлен!', status=200)

    except Exception as e:
        logger.error('Update deal request error: %s', e)
        return Response('Внутренняя ошибка сервера', status=500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=APP_PORT)
