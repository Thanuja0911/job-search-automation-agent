from abc import ABC, abstractmethod

from models.job import Job


class BaseAdapter(ABC):
    @abstractmethod
    async def fetch(self) -> list[Job]: ...
