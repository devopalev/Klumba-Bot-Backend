import source.bitrix.BitrixWorker as BW
from source.Users import Operator
from source.bitrix.Deal import Deal


def update_deal_image(user: Operator):
    photos_list = user.equip.encode_deal_photos()
    deal_data = user.deal

    # switch to previous stage first in case of repeat equip - to trigger robots properly
    if user.equip.repeating:
        BW.update_deal(deal_data.deal_id, {Deal.Fields.STAGE: Deal.FilMapStage.PROCESSED_1C})

    update_obj = {Deal.Fields.SMALL_PHOTO: [], Deal.Fields.BIG_PHOTO: [],
                  Deal.Fields.STAGE: Deal.FilMapStage.IS_EQUIPPED,
                  Deal.Fields.CLIENT_URL: user.equip.digest,
                  Deal.Fields.EQUIPER_HANDLER_ID: user.bitrix_user_id,
                  Deal.Fields.CHECKLIST: {'fileData': [user.deal.photo_name,
                                                       user.deal.photo_data]}
                  }

    for photo in photos_list:
        update_obj[Deal.Fields.SMALL_PHOTO].append({'fileData': [photo.name_small,
                                                                 photo.data_small]})
        update_obj[Deal.Fields.BIG_PHOTO].append({'fileData': [photo.name_big,
                                                               photo.data_big]})

    postcards_list = user.equip.encode_deal_postcards()
    if postcards_list:
        update_obj[Deal.Fields.POSTCARD_PHOTO] = []
        for photo in postcards_list:
            update_obj[Deal.Fields.POSTCARD_PHOTO].append({'fileData': [photo.name_big,
                                                                        photo.data_big]})

    BW.update_deal(deal_data.deal_id, update_obj)
    user.equip.clear()
