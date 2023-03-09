

# use hardcoded deals per page number to simplify logic for now
FLORISTS_PER_PAGE = 8


class UserData:
    def __init__(self):
        # to get deals for specific date
        self.florists = {}  # cached couriers of global FLORISTS (to exclude problems in case of COURIERS updated)
        self.page_number = 0
        self.total_pages = 0
        self.florist_surname_starts_with = None

    def clear(self):
        self.florists.clear()
        self.page_number = 0
        self.total_pages = 0
        self.florist_surname_starts_with = None
