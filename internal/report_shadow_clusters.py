import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_LOG = Path(r"C:\Users\Asus\Desktop\moh-assistant\logs\requests.jsonl")
DEFAULT_REPORT = Path(r"C:\Users\Asus\Desktop\moh-assistant\logs\shadow_cluster_report.txt")


def _load_rows(path: Path, tail: int | None = None, skip: int = 0) -> list[dict]:
    if not path.exists():
        return []

    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if skip > 0:
        rows = rows[skip:]
    if tail is not None and tail > 0:
        rows = rows[-tail:]
    return rows


def _format_counter(title: str, rows: list[tuple[object, int]], limit: int) -> list[str]:
    lines = [title]
    if not rows:
        lines.append("  (none)")
        return lines

    for item, count in rows[:limit]:
        lines.append(f"  {count:>4} | {item}")
    return lines


def build_report(rows: list[dict], top_n: int) -> str:
    total = len(rows)
    disagreements = [row for row in rows if row.get("shadow_family_agrees") is False]
    clarify_or_escalate = [
        row for row in rows
        if row.get("action") in {"partial_answer_with_clarify", "escalate_safety", "escalate_true_gap"}
    ]

    disagreement_counter = Counter(
        (
            row.get("shadow_family") or "unknown",
            row.get("runtime_family_proxy") or "unknown",
            row.get("action") or "unknown",
        )
        for row in disagreements
    )

    clarify_phrase_counter = Counter(
        row.get("message_normalized") or row.get("message") or ""
        for row in clarify_or_escalate
    )

    disagreement_phrase_counter = Counter(
        row.get("message_normalized") or row.get("message") or ""
        for row in disagreements
    )

    candidate_family_gaps: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in clarify_or_escalate:
        key = (
            row.get("shadow_family") or "unknown",
            row.get("runtime_family_proxy") or "unknown",
            row.get("action") or "unknown",
        )
        candidate_family_gaps[key].add(row.get("message_normalized") or row.get("message") or "")

    ranked_candidate_gaps = sorted(
        (
            key,
            len(messages),
            sorted(msg for msg in messages if msg)[:3],
        )
        for key, messages in candidate_family_gaps.items()
    )
    ranked_candidate_gaps.sort(key=lambda item: item[1], reverse=True)

    lines: list[str] = []
    lines.append("=== SHADOW CLUSTER REPORT ===")
    lines.append(f"total_rows: {total}")
    lines.append(f"disagreements: {len(disagreements)}")
    lines.append(f"clarify_or_escalate_rows: {len(clarify_or_escalate)}")
    lines.append("")

    lines.extend(_format_counter(
        "Top disagreement clusters: (shadow_family, runtime_family_proxy, action)",
        disagreement_counter.most_common(),
        top_n,
    ))
    lines.append("")

    lines.extend(_format_counter(
        "Top disagreement phrases:",
        disagreement_phrase_counter.most_common(),
        top_n,
    ))
    lines.append("")

    lines.extend(_format_counter(
        "Top clarify/escalate phrase clusters:",
        clarify_phrase_counter.most_common(),
        top_n,
    ))
    lines.append("")
    lines.append("Candidate family gaps: (shadow_family, runtime_family_proxy, action)")
    if not ranked_candidate_gaps:
        lines.append("  (none)")
    else:
        for key, unique_count, samples in ranked_candidate_gaps[:top_n]:
            lines.append(f"  {unique_count:>4} | {key}")
            if samples:
                lines.append(f"       samples: {', '.join(samples)}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize shadow-family disagreement and clarify/escalate clusters.")
    parser.add_argument("--log", default=str(DEFAULT_LOG), help="Path to requests.jsonl")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Where to write the text report")
    parser.add_argument("--top", type=int, default=10, help="How many rows to show per section")
    parser.add_argument("--tail", type=int, default=0, help="If set, summarize only the last N log rows")
    parser.add_argument("--skip", type=int, default=0, help="If set, skip the first N log rows before summarizing")
    args = parser.parse_args()

    log_path = Path(args.log)
    report_path = Path(args.report)
    tail = args.tail if args.tail > 0 else None
    rows = _load_rows(log_path, tail=tail, skip=max(args.skip, 0))
    report = build_report(rows, top_n=args.top)

    report_path.write_text(report, encoding="utf-8")
    sys.stdout.buffer.write((report + "\n\n" + f"REPORT_WRITTEN={report_path}\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
