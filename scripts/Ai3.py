from collections import Counter
from datetime import datetime
import subprocess

# ----------------------------
# File paths
# ----------------------------

# ----------------------------
# Configuration & File Paths
# ----------------------------
# NOTE: This script is currently configured for a Windows-based Snort sensor.
# If deploying on Linux, update ALERT_FILE to the appropriate path (e.g., '/var/log/snort/alert.ids')

ALERT_FILE = r"C:\Snort\log\alert.ids"        # Raw Snort alerts
SUMMARY_FILE = "stakeholder_summary.txt"     # Intermediate summary
AI_REPORT_FILE = "ai_stakeholder_report.txt" # AI-generated report

# ----------------------------
# Step 1: Parse Snort alerts
# ----------------------------
def parse_alerts(path):
    events = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 10:
                continue
            timestamp = parts[0]
            msg_start = line.find("]") + 2
            msg_end = line.find("[**]", msg_start)
            msg = line[msg_start:msg_end].strip() if msg_end > 0 else "Unknown"
            proto_start = line.find("{")
            proto_end = line.find("}", proto_start)
            proto = line[proto_start+1:proto_end] if proto_start > 0 else "?"
            arrow = line.find("->")
            if arrow > 0:
                src_part = line[proto_end+1:arrow].strip()
                dst_part = line[arrow+2:].strip()
            else:
                src_part = dst_part = "?"
            events.append({
                "time": timestamp,
                "msg": msg,
                "proto": proto,
                "src": src_part,
                "dst": dst_part,
            })
    return events

# ----------------------------
# Step 2: Summarize alerts
# ----------------------------
def summarize(events):
    summary = {}
    summary["total_alerts"] = len(events)
    summary["by_message"] = Counter(e["msg"] for e in events)
    summary["by_source"] = Counter(e["src"] for e in events)
    summary["by_proto"] = Counter(e["proto"] for e in events)
    return summary

# ----------------------------
# Step 3: Create text summary
# ----------------------------
def generate_summary_text(events, summary):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append(f"=== Snort Alert Summary ===")
    lines.append(f"Generated: {now}")
    lines.append(f"Total alerts: {summary['total_alerts']}")
    lines.append("\nMost frequent alert types:")
    for msg, count in summary["by_message"].most_common(5):
        lines.append(f"  {msg} — {count} events")
    lines.append("\nTop source IPs:")
    for src, count in summary["by_source"].most_common(5):
        lines.append(f"  {src} — {count} events")
    lines.append("\nTop protocols:")
    for proto, count in summary["by_proto"].most_common():
        lines.append(f"  {proto}: {count}")
    return "\n".join(lines)

# ----------------------------
# Step 4: Call Ollama AI
# ----------------------------
def generate_ai_report(summary_text):
    prompt = f"""
You are a cybersecurity analyst AI. Based on the following Snort alert summary,
identify the **potential power of the attack** or if it’s a simple test.
Then generate a **brief stakeholder report** and actionable **playbook suggestions**.

Snort Summary:
{summary_text}
"""

    # Run Ollama Phi-3 Mini locally
    result = subprocess.run(
        ["ollama", "run", "phi3:mini"],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120
    )

    if result.returncode != 0:
        print("❌ Ollama AI failed:", result.stderr.decode("utf-8"))
        return

    ai_output = result.stdout.decode("utf-8")

    with open(AI_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(ai_output)

    print(f"✅ AI stakeholder report saved → {AI_REPORT_FILE}")

# ----------------------------
# Step 5: Main function
# ----------------------------
def main():
    events = parse_alerts(ALERT_FILE)
    summary = summarize(events)
    summary_text = generate_summary_text(events, summary)

    # Save intermediate summary
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write(summary_text)
    print(f"Summary saved → {SUMMARY_FILE}")

    # Generate AI-enhanced report
    generate_ai_report(summary_text)

if __name__ == "__main__":
    main()
