## 🛠️ How to Build & Deploy

### Phase 1: Windows Endpoint Setup (Snort & Nmap)

**1. Core Installations**
* Download and install **[Snort 2.x](https://www.snort.org/)** for Windows. Ensure the base directory is established (e.g., `C:\Snort`).
* Download and install **[Nmap](https://nmap.org/)** on the local environment to simulate attack traffic and validate detection capabilities.

**2. Ruleset Ingestion & Tuning**
* Download the official Snort community/registered ruleset and extract it into the `C:\Snort\rules` directory.
* **Rule Tuning:** Edit the rule files to comment out (`#`) noisy or out-of-scope rules. This custom tuning narrows the focus to strictly monitor the intended testing parameters.
* **Engine Configuration:** Modify `snort.conf` to set the correct network variables (e.g., `HOME_NET`) and alter the alerting configurations to ensure logs are formatted correctly for the Python summarization script.

**3. Execution & Initial Testing**
* **Find Your Network Interface (NIC) Number:** Snort requires the specific interface index to monitor traffic. Open Command Prompt and run:
  ```cmd
  snort -W
  ```
  *(Note the index number next to your active network connection, e.g., 1, 4, or 9).*
* **Launch Snort:** Launch Command Prompt as Administrator and initialize Snort in IDS mode. Run this command: 
  ```cmd
  "C:\Snort\bin\snort.exe" -A fast -i 9 -c "C:\Snort\etc\snort.conf" -l "C:\Snort\log"
  ```
  *(Note: Tweak the `-i` interface number and `-A` alert modes to fit your specific environment and logging preferences).*
* Run targeted Nmap scans against the monitored interface to verify that the tuned rules trigger the customized alerts successfully.
* **Triggering the IDS (Loud Nmap Scan):** To verify Snort is actively catching malicious behavior, run a high-speed, aggressive port scan from another machine on the network (or against localhost if testing locally). 
  ```cmd
  nmap -T4 -A -p- [Target_IP_Address]
  ```
* Verified that the tuned Snort rules successfully detected the port sweeps and dropped the generated alerts into the `C:\Snort\log` directory, ready to be parsed by the Python UI.

---

### Phase 2: AI Integration & Interactive UI (Windows)

**1. The Local AI Engine (Ollama)**
* Ensure **[Ollama](https://ollama.com/)** is installed on the Windows host.
* Pull the preferred local LLM model via Command Prompt (e.g., Mistral or Mini) to ensure logs are processed entirely on-premise without cloud exposure.

**2. Deploying the Orchestration Scripts**
* Place the custom `Ai3.py` integration script inside the Snort logging directory (`C:\Snort\log`). This script acts as the pipeline, formatting raw Snort alerts and querying the local Ollama API.
* Launch the **Interactive UI** (built with `customtkinter`) by running the main entry script:
  ```cmd
  python protekta_app.py
  ```
  *(Note: You can open `protekta_app.py` and modify the theme, paths, or command arguments to tweak the dashboard execution according to your preferences).*

**3. Automated Incident Pipeline Validation**
* The UI actively monitors `alert.ids` for new Snort detections.
* Upon detection, the UI automatically triggers `Ai3.py`, sending the alert context to the local LLM.
* The system retrieves the generated **Mitigation Playbook** and **Shareholder Summary** and dynamically populates the local dashboard for immediate analyst review.

---

### Phase 3: Centralized Management (Kali Linux & Wazuh)

**1. Virtual Machine Provisioning**
* Deploy a **Kali Linux** virtual machine using your preferred hypervisor (e.g., VMware Workstation or VirtualBox). 
* **Hardware Requirements:** Allocate a minimum of 4GB RAM (8GB highly recommended to support the Wazuh single-node stack), 2+ CPU cores, and at least 50GB of disk space.
* **Network Configuration:** Set the network adapter to NAT or Bridged mode to ensure internet access for package updates.
* **Secure Tunneling:** Install **[Tailscale](https://tailscale.com/)** on the Kali VM to establish a secure, static internal IP. This ensures the Windows agent can consistently route telemetry to the Wazuh Manager regardless of local network changes.

**2. Wazuh Manager & Dashboard Installation**
* Launch the Kali terminal and execute the official Wazuh installation assistant to deploy the Manager, Indexer, and Dashboard.
  ```bash
  curl -sO [https://packages.wazuh.com/4.x/wazuh-install.sh](https://packages.wazuh.com/4.x/wazuh-install.sh) && sudo bash ./wazuh-install.sh -a
  ```
  *(Note: Once the script completes, securely copy the auto-generated admin passwords displayed in the terminal output).*
* **Verify Deployment:** Open a web browser on your host machine and navigate to `https://[Kali_Tailscale_IP]`. Log in with the generated credentials to confirm the Wazuh Dashboard is fully operational.
* **📚 Helpful Deployment Resources:** If you are building this in a lab and hit any snags, refer to the **[Official Wazuh Quickstart Guide](https://documentation.wazuh.com/current/quickstart.html)** or consult community troubleshooting threads on the **[r/Wazuh Subreddit](https://www.reddit.com/r/Wazuh/)**.

**3. Deploying the Wazuh Agent (Windows Endpoint)**
* In the Wazuh Dashboard, navigate to **Agents -> Deploy New Agent**. 
* Select Windows as the operating system and input the Kali VM's Tailscale IP address as the server address.
* Copy the generated PowerShell command and run it as Administrator on your Windows host to install and enroll the agent.
* Start the service using:
  ```cmd
  NET START WazuhSvc
  ```

---

### Phase 4: FIM, Threat Intel & Active Response (Wazuh + VirusTotal)

This phase configures the system to act as a fully automated Host-based Intrusion Prevention System (HIPS). It establishes File Integrity Monitoring (FIM) on a sensitive Windows directory, cross-references any dropped files with VirusTotal, and instantly deletes confirmed malware.

**1. Configure FIM on the Windows Endpoint**
* **Target Machine:** Windows (Wazuh Agent)
* **File to Edit:** `C:\Program Files (x86)\ossec-agent\ossec.conf`
* **Action:** Open the file as Administrator, locate the `<syscheck>` section, and add the directory you want to protect. Ensure real-time monitoring and whodata are enabled.
  ```xml
  <directories realtime="yes" check_all="yes" report_changes="yes">C:\Users\Administrator\Desktop\Sensitive_Folder</directories>
  ```
* Restart the Wazuh service via Command Prompt: `NET START WazuhSvc`

**2. Integrate the VirusTotal API**
* **Target Machine:** Kali Linux (Wazuh Manager)
* **File to Edit:** `/var/ossec/etc/ossec.conf`
* **Action:** Obtain a free API key from your **[VirusTotal API Dashboard](https://www.virustotal.com/gui/my-apikey)**. Open the manager's configuration file and append the integration block below. This instructs Wazuh to query VT every time the FIM engine detects a new or modified file.
  ```xml
  <integration>
    <name>virustotal</name>
    <api_key>YOUR_VIRUSTOTAL_API_KEY_HERE</api_key>
    <rule_id>554,550</rule_id>
    <alert_format>json</alert_format>
  </integration>
  ```

**3. Configure Automated Malware Deletion (Active Response)**
* **Target Machine:** Kali Linux (Wazuh Manager)
* **File to Edit:** `/var/ossec/etc/ossec.conf`
* **Action:** Define the Active Response command to trigger the built-in Windows file removal script whenever VirusTotal returns a positive malware hit (Rule ID `87105` corresponds to a VirusTotal positive match).
  ```xml
  <command>
    <name>remove-threat</name>
    <executable>remove-threat.cmd</executable>
    <timeout_allowed>no</timeout_allowed>
  </command>

  <active-response>
    <command>remove-threat</command>
    <location>local</location>
    <rules_id>87105</rules_id>
  </active-response>
  ```
* **Finalize:** Restart the Wazuh Manager to apply the entire IPS pipeline:
  ```bash
  sudo systemctl restart wazuh-manager
  ```

**4. Verification & Testing (The EICAR Threat Simulation)**
* **Action:** To safely validate the end-to-end automated detection and remediation pipeline, drop an industry-standard EICAR malware test string into your monitored Windows directory.
* Open PowerShell on the Windows host and execute the following command to generate the test file:
  ```powershell
  Set-Content -Path "C:\Users\Administrator\Desktop\Sensitive_Folder\eicar.com" -Value 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
  ```
* **Automated Defensive Pipeline Execution:** 1. The Wazuh FIM engine instantly captures the file creation event.
  2. The Wazuh Manager intercepts the log and automatically queries the VirusTotal API with the file's cryptographic hash.
  3. VirusTotal returns a positive malicious detection.
  4. The Active Response engine immediately fires, executing `remove-threat.cmd` to wipe `eicar.com` from the system within seconds of creation.
* **Viewing the Security Events in the Wazuh Dashboard:**
  1. Open a web browser and access your Wazuh Dashboard interface.
  2. Navigate to the top menu and select **Modules ➔ Security Events**.
  3. Click on the **Events** tab to access the raw telemetry stream.
  4. In the query search bar, filter specifically for the threat intelligence hits by typing: `rule.id:87105` (or check for `rule.id:550` to see the initial FIM creation alert).
  5. Expand the logged event to view the full JSON payload, validating the mitigation.

---

### Phase 5: Network Deep Packet Inspection & Centralized Logging

With the host-based defenses active, this phase configures Suricata on the Kali VM for deep packet inspection and routes both Suricata and Snort telemetry directly into the Wazuh SIEM for a unified, single-pane-of-glass view.

**1. Suricata Installation & Configuration (Kali VM)**
* **Target Machine:** Kali Linux
* Install Suricata via the package manager:
  ```bash
  sudo apt update && sudo apt install suricata -y
  ```
* **File to Edit:** `/etc/suricata/suricata.yaml`
* **Action:** Open the configuration file to optimize the network engine. You must modify the network variables to match your environment.
  * **Network Range:** Locate the `HOME_NET` variable and replace the default IP with your specific local subnet (e.g., `192.168.1.0/24`) or your Tailscale VPN subnet.
  * **Capture Interface:** Locate the `af-packet` section and change the default `interface` from `eth0` to your active monitoring interface. *(Note: You can run `ip a` in the terminal to verify your active interface).*
* Start and enable the Suricata service:
  ```bash
  sudo systemctl enable suricata && sudo systemctl restart suricata
  ```

**2. Ingesting Suricata Logs into Wazuh**
* **Target Machine:** Kali Linux (Wazuh Manager)
* **File to Edit:** `/var/ossec/etc/ossec.conf`
* **Action:** Wazuh includes native JSON decoders for Suricata. Add a `localfile` block to instruct the manager to read Suricata's `eve.json` output file.
  ```xml
  <localfile>
    <log_format>json</log_format>
    <location>/var/log/suricata/eve.json</location>
  </localfile>
  ```
* Restart the Wazuh Manager to apply the ingestion pipeline:
  ```bash
  sudo systemctl restart wazuh-manager
  ```

**3. Ingesting Snort Logs into Wazuh**
* **Target Machine:** Windows (Wazuh Agent)
* **File to Edit:** `C:\Program Files (x86)\ossec-agent\ossec.conf`
* **Action:** Similar to Suricata, we need to instruct the Windows agent to pull the local Snort alerts and push them up to the Kali manager. Open the configuration file as Administrator and add this block:
  ```xml
  <localfile>
    <log_format>snort-fast</log_format>
    <location>C:\Snort\log\alert.ids</location>
  </localfile>
  ```
* Restart the Wazuh agent via Command Prompt to begin forwarding the logs:
  ```cmd
  NET STOP WazuhSvc && NET START WazuhSvc
  ```

---

### Phase 6: Automated Firewall Mitigation & Severity Tiering (Active Response)

This phase configures the Wazuh Active Response engine to dynamically block attacking IPs at the firewall level. The system is tiered to trigger automated containment protocols only when security events cross a high-severity threshold (e.g., Alert Level 10 or higher), preventing network disruption from low-level anomalies.

**Option A: Native Firewall Drop (Kali Linux / Linux Gateway)**
* **Target Machine:** Kali Linux (Wazuh Manager / Gateway)
* **File to Edit:** `/var/ossec/etc/ossec.conf`
* **Action:** Open the configuration file and define the firewall command utilizing Wazuh's pre-compiled standard defense script (`firewall-drop`). Then, configure the active-response block to trigger globally whenever any rule hits **Level 10** or above.
  ```xml
  <command>
    <name>firewall-drop</name>
    <executable>firewall-drop</executable>
    <timeout_allowed>yes</timeout_allowed>
  </command>

  <active-response>
    <command>firewall-drop</command>
    <location>local</location>
    <level>10</level>
    <timeout>1800</timeout>
  </active-response>
  ```

**Option B: Custom Script Execution (Python Integration Pipeline)**
* **Target Machine:** Kali Linux or Windows Endpoint (Depending on script location)
* **File to Edit:** `/var/ossec/etc/ossec.conf`
* **Action:** If you prefer to handle containment via a custom automation script (e.g., standardizing your containment actions inside a dedicated Python toolkit), place your script inside the active response directory (`/var/ossec/active-response/bin/` on Linux or `C:\Program Files (x86)\ossec-agent\active-response\bin\` on Windows). 
* Define the execution parameters inside the manager's configuration file:
  ```xml
  <command>
    <name>custom-python-firewall</name>
    <executable>custom_firewall_kick.py</executable>
    <timeout_allowed>no</timeout_allowed>
  </command>

  <active-response>
    <command>custom-python-firewall</command>
    <location>local</location>
    <level>12</level>
  </active-response>
  ```

**3. Applying and Verifying the Rules**
* Restart the Wazuh Manager daemon to initialize the new active defense layers:
  ```bash
  sudo systemctl restart wazuh-manager
  ```
* **Validation Method:** Simulate an aggressive attack vector (such as an intensive brute-force SSH attack using Hydra or a loud Nmap port sweep) against the monitored interface to intentionally trigger a high-level alert.
* **Verification:** 1. Once the alert crosses the defined threshold (e.g., Level 10), attempt to `ping` the target machine from the attacker IP. The ICMP packets will immediately drop or time out, proving the firewall rule successfully injected.
  2. Open the Wazuh Dashboard and navigate to **Modules ➔ Security Events**.
  3. Search the events query bar for `rule.id:651` to view the explicit "Host Blocked by firewall-drop Active Response" log, validating the automated pipeline.

---

### Phase 7: UI-Driven Alerting & Custom Email Notifications (OpenSearch)

This phase configures the Wazuh Dashboard's native Alerting and Notifications engine to route critical security events out-of-band. Instead of relying on backend configuration files, we establish graphical Monitors and Channels to dynamically email analysts when specific threat thresholds are breached.

**1. Create the Notification Channel (Destination)**
First, we define *where* the alerts will be sent and how they authenticate.
* **Navigation:** Open the Wazuh Dashboard. Click the top-left menu icon and navigate to **Explore ➔ Notifications**.
* **Action:** Click **Channels** and select **Create channel**.
* **Configuration:**
  * **Name:** `Security_Team_Email`
  * **Channel Type:** Select **Email** (Note: You can also easily route to Slack, Teams, or PagerDuty using webhooks here).
  * **SMTP Sender:** Configure your SMTP details (e.g., Gmail SMTP using an App Password). 
  * **Default Recipients:** Add your destination email address.
* Click **Create** to lock in the routing destination.

**2. Create the Alerting Monitor (The Listener)**
Next, we tell the system exactly which logs to listen for in real-time.
* **Navigation:** Open the top-left menu and navigate to **Explore ➔ Alerting**.
* **Action:** Click **Monitors** and select **Create monitor**.
* **Configuration:**
  * **Monitor Name:** `Critical-Threat-Monitor`
  * **Monitor Type:** Select **Per query monitor**.
  * **Method:** Select **Visual editor**.
  * **Data Source (Index):** `wazuh-alerts-*` (This ensures we are querying the active alert stream).
  * **Data Filter:** Set your threshold. For example, to listen for high-level threats, set the filter to: `rule.level is greater than or equal to 12` (or specify an exact `rule.id`).
* Click **Create** to start the listener.

**3. Define the Trigger & Custom Action Message**
Finally, we define what happens when the Monitor catches a matching log, and we customize the email payload.
* **Action:** Inside your newly created Monitor, scroll down and click **Add trigger**.
* **Trigger Name:** `High-Severity-Trigger`
* **Severity Level:** `1 (Highest)`
* **Configure Actions:** Scroll down to the Actions section.
  * **Action Name:** `Send-Email-Alert`
  * **Destination:** Select the `Security_Team_Email` channel you created in Step 1.
  * **Message Subject:** `🚨 PROTEKTA Critical Alert: {{ctx.results.0.hits.hits.0._source.rule.description}}`
  * **Message Body:** You can use Mustache templating to pull exact data from the log into your email. 
    ```text
    PROTEKTA Security System has intercepted a critical event.
    
    Threat Level: {{ctx.results.0.hits.hits.0._source.rule.level}}
    Rule Description: {{ctx.results.0.hits.hits.0._source.rule.description}}
    Target Agent: {{ctx.results.0.hits.hits.0._source.agent.name}}
    Attacker IP: {{ctx.results.0.hits.hits.0._source.data.srcip}}
    
    Please log into the Wazuh Dashboard immediately for full triage.
    ```
* Click **Save**.

**4. Verification & Testing**
* To validate the UI pipeline, generate an alert that breaches your defined threshold (e.g., executing the EICAR test file to trigger a Level 12+ VirusTotal hit).
* The Wazuh Indexer will instantly evaluate the log against the Monitor, fire the Trigger, and execute the Action.
* Check your email inbox to verify receipt of the beautifully formatted, custom templated alert message.

---

## 📊 End-to-End System Verification

To ensure all independent layers of PROTEKTA are communicating smoothly across the hybrid environment, follow this operational checklist:

1. **The Ingestion Pipeline:** Run a localized test on the Windows endpoint. Verify that Snort alerts are written to `alert.ids` and that the local Wazuh Agent successfully ships the log upstream to the Kali Manager.
2. **The SIEM Single Pane of Glass:** Log into the Wazuh Dashboard. Navigate to the Discover tab and verify that indexes are actively populated by three distinct log streams:
   * Host security events (`wazuh-alerts-*`)
   * Network deep packet inspection streams (`Suricata eve.json`)
   * Windows perimeter events (`Snort alert.ids`)
3. **The AI Automated Response Loop:** Drop an EICAR test string into the protected directory. Confirm via the local Python UI that the Snort summarizer feeds the alert context into the local Ollama LLM, and verify your email inbox receives the custom OpenSearch threshold notification within seconds.

---