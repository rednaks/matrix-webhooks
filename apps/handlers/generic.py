from abc import ABC, abstractmethod


class GenericHandler(ABC):

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    @abstractmethod
    def parse(self, payload):
        ...
