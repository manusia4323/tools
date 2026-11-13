"""Struktur data untuk temuan dan hasil pemeriksaan."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Finding:
    type: str
    severity: str
    url: str
    evidence: str
    confidence: str = "medium"
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanResult:
    target: str
    started_at: str
    finished_at: str = ""
    tool_version: str = "1.0"
    findings: list[Finding] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
