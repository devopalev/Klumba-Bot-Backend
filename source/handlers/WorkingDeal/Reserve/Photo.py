# storing small and big versions of the same photo
import base64


class Photo:
    data_big = None  # raw / encoded
    name_big = None

    def __init__(self, name_big, data_big):
        self.data_big = data_big
        self.name_big = name_big

    def b64_encode(self):
        self.data_big = base64.b64encode(self.data_big).decode('ascii')
