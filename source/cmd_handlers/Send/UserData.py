

# use hardcoded deals per page number to simplify logic for now
COURIERS_PER_PAGE = 8


class UserData:
    def __init__(self):
        # to get deals for specific date
        self.couriers = {}  # cached couriers of global COURIERS (to exclude problems in case of COURIERS updated)
        self.page_number = 0
        self.total_pages = 0
        self.courier_surname_starts_with = None

    def clear(self):
        self.couriers.clear()
        self.page_number = 0
        self.total_pages = 0
        self.courier_surname_starts_with = None
