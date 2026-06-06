import customtkinter as ctk
import subprocess
import threading
import time
import os

# --- Configuration ---
# PATHS: Update these if your location is different
SNORT_CMD = r'"C:\Snort\bin\snort.exe" -A fast -i 9 -c "C:\Snort\etc\snort.conf" -l "C:\Snort\log"'
LOG_DIR = r"C:\Snort\log"

# We will look for these base names. The code below checks for .txt automatically.
FILE_Alert = "alert.ids"
FILE_Report = "ai_stakeholder_report"
FILE_Summary = "stakeholder_summary"

# Theme Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class ProtektaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("PROTEKTA | AI-Enhanced IPS")
        self.geometry("1100x700")
        self.configure(fg_color="#050505")

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#101010")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="PROTEKTA", font=("Roboto Medium", 24), text_color="#A020F0").pack(pady=30)

        self.start_btn = ctk.CTkButton(
            self.sidebar, 
            text="INITIALIZE SENTINEL", 
            command=self.start_snort,
            fg_color="#4B0082", 
            hover_color="#6A0DAD"
        )
        self.start_btn.pack(pady=20, padx=20)

        self.status_label = ctk.CTkLabel(self.sidebar, text="STATUS: IDLE", text_color="gray")
        self.status_label.pack(side="bottom", pady=20)

        # --- Main Area ---
        self.main_frame = ctk.CTkFrame(self, fg_color="#050505")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # 1. Alert Feed
        self.alert_frame = ctk.CTkFrame(self.main_frame, fg_color="#121212", border_color="#A020F0", border_width=1)
        self.alert_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 20))
        ctk.CTkLabel(self.alert_frame, text="LIVE THREAT FEED", text_color="white").pack(anchor="w", padx=10)
        self.alert_box = ctk.CTkTextbox(self.alert_frame, text_color="#00FF00", fg_color="#000000", font=("Consolas", 12))
        self.alert_box.pack(fill="both", expand=True, padx=5, pady=5)

        # 2. AI Report
        self.report_frame = ctk.CTkFrame(self.main_frame, fg_color="#121212", border_color="#333333", border_width=1)
        self.report_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(self.report_frame, text="AI STAKEHOLDER REPORT", text_color="#D1D1D1").pack(anchor="w", padx=10)
        self.report_box = ctk.CTkTextbox(self.report_frame, text_color="#E0E0E0", fg_color="#1A1A1A")
        self.report_box.pack(fill="both", expand=True, padx=5, pady=5)

        # 3. Summary
        self.summary_frame = ctk.CTkFrame(self.main_frame, fg_color="#121212", border_color="#333333", border_width=1)
        self.summary_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(self.summary_frame, text="EXECUTIVE SUMMARY", text_color="#D1D1D1").pack(anchor="w", padx=10)
        self.summary_box = ctk.CTkTextbox(self.summary_frame, text_color="#E0E0E0", fg_color="#1A1A1A")
        self.summary_box.pack(fill="both", expand=True, padx=5, pady=5)

        # Logic Variables
        self.snort_process = None
        self.last_alert_content = ""
        self.monitoring_active = False

    def start_snort(self):
        """Starts Snort and the polling loop."""
        if self.monitoring_active: return

        try:
            # Start Snort
            self.snort_process = subprocess.Popen(SNORT_CMD, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.status_label.configure(text="STATUS: MONITORING", text_color="#00FF00")
            self.start_btn.configure(state="disabled", fg_color="#222222")
            
            # Start the infinite checking loop
            self.monitoring_active = True
            self.check_files_loop()
            
        except Exception as e:
            self.alert_box.insert("end", f"[ERROR] Start failed: {e}\n")

    def check_files_loop(self):
        """Checks for file updates every 1 second."""
        if not self.monitoring_active: return

        # 1. Check Alert File
        alert_path = os.path.join(LOG_DIR, FILE_Alert)
        content = self.read_file_safe(alert_path)
        
        # If content changed, update UI and Trigger AI
        if content and content != self.last_alert_content:
            self.last_alert_content = content
            self.alert_box.delete("1.0", "end")
            self.alert_box.insert("end", content)
            self.alert_box.see("end")
            
            # Trigger AI logic in a separate thread
            threading.Thread(target=self.run_ai_sequence, daemon=True).start()

        # 2. Check Report (Try both no-extension and .txt)
        report_content = self.read_file_safe(os.path.join(LOG_DIR, FILE_Report))
        if not report_content: 
            report_content = self.read_file_safe(os.path.join(LOG_DIR, FILE_Report + ".txt"))
        
        if report_content:
             self.update_box_if_new(self.report_box, report_content)

        # 3. Check Summary (Try both no-extension and .txt)
        summary_content = self.read_file_safe(os.path.join(LOG_DIR, FILE_Summary))
        if not summary_content: 
            summary_content = self.read_file_safe(os.path.join(LOG_DIR, FILE_Summary + ".txt"))

        if summary_content:
            self.update_box_if_new(self.summary_box, summary_content)

        # Schedule next check in 1000ms (1 second)
        self.after(1000, self.check_files_loop)

    def run_ai_sequence(self):
        """Pauses, runs Ai3.py, then loop handles the UI update."""
        self.status_label.configure(text="STATUS: AI ANALYZING...", text_color="orange")
        time.sleep(2) # Pause 2 seconds
        
        ai_script_path = os.path.join(LOG_DIR, "Ai3.py")
        try:
            subprocess.run(["python", ai_script_path], check=True)
            self.status_label.configure(text="STATUS: MONITORING", text_color="#00FF00")
        except Exception as e:
            print(f"AI Script Error: {e}")
            self.status_label.configure(text="STATUS: AI ERROR", text_color="red")

    def read_file_safe(self, filepath):
        """Returns file content or None if file doesn't exist."""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return f.read()
            except:
                return None
        return None

    def update_box_if_new(self, textbox, new_content):
        """Updates text box only if content is different."""
        current_text = textbox.get("1.0", "end-1c")
        if new_content != current_text:
            textbox.delete("1.0", "end")
            textbox.insert("1.0", new_content)
            textbox.see("end")

if __name__ == "__main__":
    app = ProtektaApp()
    app.mainloop()