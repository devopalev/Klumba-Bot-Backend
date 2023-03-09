from typing import List
from source.DealData import DealData


class UserData:
    def __init__(self):
        self.deals_list: List[DealData] = []
        self.cur_deal_index = 0

    def add_deal(self, deal: DealData):
        self.deals_list.append(deal)

    def clear(self):
        self.deals_list.clear()
        self.cur_deal_index = 0
