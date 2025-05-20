# pipelines/pipeline.py

from abc import ABC, abstractmethod

class Pipeline(ABC):
    @abstractmethod
    def run(self) -> None:
        """Run the pipeline logic."""
        pass