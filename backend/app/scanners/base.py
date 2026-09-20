"""
Abstract base classes and interfaces for AegisScan security scanner adapters.
"""

import abc
from typing import Dict, Any, List, Optional
from app.models.scan_job import ScannerEngineType, ScanJobStatus


class ScannerAdapter(abc.ABC):
    """
    Abstract interface for security testing engine adapters.
    Phase 3 implements clean stubs returning NOT_IMPLEMENTED (zero fake results).
    Real execution will be wired in Phase 4.
    """

    @abc.abstractmethod
    def name(self) -> str:
        """Return the human-readable identifier of this scanner."""
        pass

    @abc.abstractmethod
    def engine_type(self) -> ScannerEngineType:
        """Return the ScannerEngineType enum associated with this adapter."""
        pass

    @abc.abstractmethod
    def validate_config(self, config: Optional[Dict[str, Any]]) -> bool:
        """Validate if the scanner configuration is valid and safe."""
        pass

    @abc.abstractmethod
    def prepare(self, assessment_id: int, target: str, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare execution parameters, rule selections, and target manifests."""
        pass

    @abc.abstractmethod
    def is_available(self) -> tuple[bool, Optional[str]]:
        """Return whether the scanner can execute on this host and its path."""
        pass

    @abc.abstractmethod
    async def execute(self, job_id: int, assessment_id: int, target: str, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute scanner execution.
        In Phase 3, returns NOT_IMPLEMENTED without fake results.
        """
        pass

    @abc.abstractmethod
    def cancel(self, job_id: int) -> bool:
        """Cancel a running scanner process."""
        pass

    @abc.abstractmethod
    def parse_results(self, result_location: Optional[str]) -> List[Dict[str, Any]]:
        """Parse raw scanner findings into normalized records."""
        pass
