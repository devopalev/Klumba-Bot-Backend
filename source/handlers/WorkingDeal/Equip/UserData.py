from typing import List
from .Photo import Photo


class UserData:
    def __init__(self):
        self.photos: List[Photo] = []
        self.postcard_front: Photo = None
        self.postcard_reverse: Photo = None
        self.digest = str()
        # repeating equip
        self.repeating = False

    def add_deal_photo(self, photo):
        self.photos.append(photo)

    def clear(self):
        self.photos.clear()
        self.postcard_front = None
        self.postcard_reverse = None
        self.digest = str()
        self.repeating = False

    def encode_deal_photos(self):
        for p in self.photos:
            p.b64_encode()

        return self.photos

    def encode_deal_postcards(self):
        self.postcard_front.b64_encode()
        self.postcard_reverse.b64_encode()
        return [self.postcard_front, self.postcard_reverse]

