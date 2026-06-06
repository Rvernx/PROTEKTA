#!/usr/bin/env python3
import sys
import json
import os
import datetime

# Log file for PROTEKTA active responses
LOG_FILE = "/var/ossec/logs/active-responses.log"

def log_action(msg):
    """Writes actions to the Wazuh active response log with a timestamp."""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} active-response/bin/remove-threat.py: {msg}\n")

def main():
    # Wazuh sends the alert payload via standard input
    input_data = sys.stdin.readline()
    if not input_data:
        return

    try:
        # Parse the JSON payload
        alert = json.loads(input_data)
        
        # In Wazuh 4.x, active response data is nested under "parameters" -> "alert"
        parameters = alert.get("parameters", {})
        alert_data = parameters.get("alert", alert)
        
        # Extract the file path of the malicious file
        # This is typically found in the syscheck (FIM) section of a VirusTotal alert
        file_path = alert_data.get("syscheck", {}).get("path")
        
        # Fallback extraction just in case the JSON structure shifts
        if not file_path:
            file_path = alert_data.get("data", {}).get("virustotal", {}).get("source", {}).get("file")

        # Execute the Threat Removal
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            log_action(f"[PROTEKTA SUCCESS] Deleted malicious file identified by VirusTotal: {file_path}")
        elif file_path:
            log_action(f"[PROTEKTA INFO] File not found or already deleted: {file_path}")
        else:
            log_action("[PROTEKTA ERROR] Could not extract a valid file path from the VirusTotal alert payload.")

    except json.JSONDecodeError:
        log_action("[PROTEKTA ERROR] Failed to parse JSON payload from Wazuh.")
    except Exception as e:
        log_action(f"[PROTEKTA CRITICAL] Unexpected error during threat removal: {str(e)}")

if __name__ == "__main__":
    main()