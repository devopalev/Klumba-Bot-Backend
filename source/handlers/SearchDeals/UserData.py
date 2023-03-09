import datetime
from typing import Dict, List
import uuid

from source.bitrix.Deal import Deal


class BaseFilter:
    pass


class FilterDate:
    def __init__(self):
        self._start: datetime.datetime = None
        self._end: datetime.datetime = None

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        self._start = value

    @start.deleter
    def start(self):
        self._start = None

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value):
        self._end = value

    @end.deleter
    def end(self):
        self._end = None

    @property
    def empty(self):
        return not any((self._start, self._end))


class Template:
    def __init__(self, template_id, name):
        self.id = template_id
        self.name = name
        self.filter_date = FilterDate()
        self.filter_stage = []
        self.filter_subdivisions = []
        self.filter_districts = []
        self.filter_payment_type = []
        self.filter_payment_method = []
        self.filter_roles = []

    def rename(self, name):
        self.name = name

    def reset(self):
        self.__init__(self.id, self.name)

    @property
    def empty(self):
        return not any([not self.filter_date.empty, self.filter_stage, self.filter_subdivisions, self.filter_districts,
                        self.filter_payment_type, self.filter_payment_method])


class Templates:
    def __init__(self):
        self._storage: Dict[str: Template] = {}
        default = Template(self._generator_id(), name="Фильтр по умолчанию")
        self._storage[default.id] = default
        self._selected = default

    def __len__(self):
        return len(self._storage)

    def _generator_id(self):
        while True:
            key = uuid.uuid4().hex[:8]
            if key not in self._storage:
                return key

    def create(self, name: str):
        template = Template(self._generator_id(), name)
        self._storage[template.id] = template
        self._selected = template

    def reset_selected(self):
        self._selected.reset()

    def delete(self) -> None:
        if len(self._storage) > 1:
            self._storage.pop(self._selected.id)
            self._selected = list(self._storage.values())[0]

    def rename(self, name):
        self._selected.rename(name)

    def select(self, template_id):
        template = self._storage.get(template_id)
        if template is not None:
            self._selected = template
            return True
        return False

    @property
    def selected(self):
        return self._selected

    @property
    def storage(self) -> dict:
        return self._storage


class FiltersDealData:
    class Meta:
        date_start = "Дата от"
        time_start = "Время от"
        date_end = "Дата до"
        time_end = "Время до"

        stage = "Состояния сделки"
        shop_performer = "Магазины исполнители"
        collector = "Сборщик"

    class DateFilter:
        def __init__(self, d_start, t_start, d_end, t_end):
            self.date_start = None
            self.time_start = None
            self.date_end = None
            self.time_end = None

    def __init__(self):
        self.date: FiltersDealData.DateFilter = None
        self.stage = []
        self.shop_performer = []
        self.collector = None

    def get_filters(self):
        return self.__dict__


class ResultSearch:
    def __init__(self):
        self.deals: List[Deal] = []
        self.page = 0

    def clear(self):
        self.deals.clear()
