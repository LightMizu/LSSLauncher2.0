from abc import ABC, abstractmethod

class Navigator(ABC):
    @abstractmethod
    def navigate_to(self, screen_name: str):
        pass