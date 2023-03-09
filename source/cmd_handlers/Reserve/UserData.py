from typing import List
from .Photo import Photo


class UserData:
    def __init__(self):
        self.photos: List[Photo] = []

    def add_deal_photo(self, photo):
        self.photos.append(photo)

    def clear(self):
        self.photos.clear()

    def encode_deal_photos(self):
        for p in self.photos:
            p.b64_encode()

        return self.photos
