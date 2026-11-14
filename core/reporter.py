"""Render hasil pemeriksaan ke terminal, JSON, atau Markdown."""

import json
from collections import Counter
from pathlib import Path

from core.logger import PirateLogger as Log
from core.models import ScanResult


class Reporter:
    def __init__(self, result: ScanResult) -> None:
        self.result = result

    def to_terminal(self, skip_types: set[str] | None = None) -> None:
        counts = Counter(finding.severity for finding in self.result.findings)
        if not self.result.findings:
            Log.info("No findings.")
        else:
            log_by_severity = {
                "info": Log.info,
                "low": Log.info,
                "medium": Log.warn,
                "high": Log.bad,
            }
            for finding in self.result.findings:
                if skip_types is not None and finding.type in skip_types:
                    continue
                log = log_by_severity.get(finding.severity, Log.info)
                log(
                    f"[{finding.severity}] {finding.type}  "
                    f"{finding.url}  ({finding.evidence})"
                )

        Log.info(
            "Finished. "
            f"{len(self.result.findings)} findings "
            f"({counts['high']} high, {counts['medium']} medium, "
            f"{counts['low']} low, {counts['info']} info)."
        )

    def to_json(self, path: str) -> str:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(
                self.result.to_dict(),
                output_file,
                indent=2,
                ensure_ascii=False,
            )
        Log.good(f"JSON report saved to {path}")
        return path

    def to_markdown(self, path: str) -> str:
        lines = [
            "# The Pirates — Report",
            "",
            f"**Target:** {self.result.target}",
            f"**Started:** {self.result.started_at}",
            f"**Finished:** {self.result.finished_at}",
            f"**Tool Version:** {self.result.tool_version}",
            "",
            "| Severity | Type | URL | Evidence |",
            "|---|---|---|---|",
        ]
        for finding in self.result.findings:
            values = (
                finding.severity,
                finding.type,
                finding.url,
                finding.evidence,
            )
            escaped = tuple(
                str(value).replace("|", r"\|").replace("\r", " ").replace("\n", " ")
                for value in values
            )
            lines.append(f"| {' | '.join(escaped)} |")

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        Log.good(f"Markdown report saved to {path}")
        return path