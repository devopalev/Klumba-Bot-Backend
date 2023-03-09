# storing small and big versions of the same photo
import base64


class Photo:
    data_small = None  # raw / encoded
    data_big = None  # raw / encoded
    name_small = None
    name_big = None
    state = None

    INITIALIZED_AS_BINARY = 1
    IS_ON_DISK = 2
    IS_ENCODED = 3

    def __init__(self, name_small=None, name_big=None, data_small=None, data_big=None):
        self.data_small = data_small
        self.data_big = data_big
        self.name_small = name_small
        self.name_big = name_big
        self.state = Photo.INITIALIZED_AS_BINARY

    def b64_encode(self):
        if self.data_small:
            self.data_small = base64.b64encode(self.data_small).decode('ascii')

        if self.data_big:
            self.data_big = base64.b64encode(self.data_big).decode('ascii')

        self.state = Photo.IS_ENCODED

    def save_big(self, f):
        if self.state == Photo.INITIALIZED_AS_BINARY:
            bytes_written = f.write(self.data_big)
            if bytes_written != len(self.data_big):
                raise Exception("Error writing binary data of photo: inconsistent write attempt")

            self.state = Photo.IS_ON_DISK

    def has_been_saved(self):
        return self.state != Photo.INITIALIZED_AS_BINARY
