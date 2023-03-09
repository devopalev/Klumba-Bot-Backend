from typing import List
from .Photo import Photo


class UserData:
    def __init__(self):
        self.photos: List[Photo] = []
        self.postcards: List[Photo] = []
        self.digest = str()
        # repeating equip
        self.repeating = False

    def add_deal_photo(self, photo):
        self.photos.append(photo)

    def add_deal_postcard(self, photo):
        self.postcards.append(photo)

    def clear(self):
        self.photos.clear()
        self.postcards.clear()
        self.digest = str()
        self.repeating = False

    def encode_deal_photos(self):
        for p in self.photos:
            p.b64_encode()

        return self.photos

    def encode_deal_postcards(self):
        for p in self.postcards:
            p.b64_encode()

        return self.postcards
