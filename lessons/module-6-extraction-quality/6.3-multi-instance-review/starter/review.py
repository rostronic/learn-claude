"""Review tool schema + confidence routing for chapter 6.3.

REVIEW_TOOL is the structured-output tool a reviewer instance is forced to call:
its input is a list of findings, each carrying a confidence score (for calibrated
routing) and a detected_pattern (so you can later analyze which constructs trigger
false positives when developers dismiss findings).
"""

REVIEW_TOOL = {
    "name": "report_findings",
    "description": "Report code-review findings as structured data.",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string"},
                        "issue": {"type": "string"},
                        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                        # Self-reported confidence enables calibrated review routing.
                        "confidence": {"type": "number"},
                        # Which construct triggered the finding — for false-positive analysis.
                        "detected_pattern": {"type": "string"},
                    },
                    "required": ["file", "issue", "severity", "confidence"],
                },
            },
        },
        "required": ["findings"],
    },
}
