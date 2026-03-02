# Ramon Solis
# Feb 27, 2026
#
# Meraki Dashboard Tools API GUI Edition by Ramon Solis
#
# pip install meraki fpdf2 matplotlib python-dotenv
# Compiler pyinstaller --onefile --noconsole Script.py
# _____________________________________________________
import gc
import re
import meraki
from fpdf import FPDF
from datetime import datetime
import sys
import os
import time
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from dotenv import load_dotenv

# ----------------------------
# Global Variables
# ----------------------------
dashboard = None
ORG_ID = None

# ----------------------------
# Helper Functions
# ----------------------------
def speed_to_mbps(speed_value):
    if speed_value is None:
        return None
    if isinstance(speed_value, (int, float)):
        return int(speed_value)
    if isinstance(speed_value, str):
        s = speed_value.strip().lower()
        if s.isdigit():
            return int(s)
        m = re.search(r"(\d+(\.\d+)?)\s*(g|m)bps", s)
        if m:
            value = float(m.group(1))
            unit = m.group(3)
            return int(value * 1000) if unit == "g" else int(value)
    return None

def generate_pdf_report(title, headers, col_widths, data_rows, filename):
    pdf = FPDF(orientation='L') 
    pdf.add_page()
    current_date = datetime.now().strftime("%B %d, %Y - %H:%M:%S")
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt=title, ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, txt=f"Generated on: {current_date}", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    for i in range(len(headers)):
        pdf.cell(col_widths[i], 10, headers[i], border=1, align='C')
    pdf.ln()
    
    pdf.set_font("Arial", '', 10)
    for row in data_rows:
        for i in range(len(row)):
            cell_text = str(row[i])[:45] 
            pdf.cell(col_widths[i], 10, cell_text, border=1)
        pdf.ln()
        
    pdf.output(filename)
    print(f"[+] PDF Report successfully saved to: {filename}")


# ----------------------------
# Core Tool Functions
# ----------------------------
def tool_slow_aps(make_pdf=True):
    if make_pdf: print("\nScanning for slow APs...")
    data_rows = []
    ap_statuses = dashboard.wireless.getOrganizationWirelessDevicesEthernetStatuses(ORG_ID, total_pages='all')

    for ap in ap_statuses:
        ap_name = ap.get("name", "Unnamed AP")
        ap_serial = ap.get("serial")
        for port in ap.get("ports", []):
            raw_speed = port.get("linkNegotiation", {}).get("speed")
            speed_mbps = speed_to_mbps(raw_speed)

            if speed_mbps is not None and speed_mbps < 1000:
                upstream_switch, upstream_port = "Unknown Switch", "Unknown Port"
                try:
                    neighbors = dashboard.devices.getDeviceLldpCdp(ap_serial)
                    if isinstance(neighbors, dict) and "ports" in neighbors:
                        for _, p_data in neighbors["ports"].items():
                            if not isinstance(p_data, dict):
                                continue
                            if "cdp" in p_data and isinstance(p_data["cdp"], dict):
                                upstream_switch = p_data["cdp"].get("deviceId", upstream_switch)
                                upstream_port = p_data["cdp"].get("portId", upstream_port)
                                break
                            if "lldp" in p_data and isinstance(p_data["lldp"], dict):
                                upstream_switch = p_data["lldp"].get("systemName", upstream_switch)
                                upstream_port = p_data["lldp"].get("portId", upstream_port)
                except meraki.APIError:
                    pass
                data_rows.append([ap_name, f"{speed_mbps} Mbps", upstream_switch, upstream_port])

    if make_pdf:
        if data_rows:
            print(f"\n[+] Found {len(data_rows)} slow APs:")
            for r in data_rows:
                print(f"  - {r[0]} ({r[1]}) -> Switch: {r[2]}")
            generate_pdf_report("Meraki APs Running Below 1 Gbps", ['AP Name', 'Current Speed', 'Upstream Switch', 'Switch Port'], [80, 40, 90, 60], data_rows, "Report_Slow_APs.pdf")
        else:
            print("\n[+] Good news: No slow APs found! PDF skipped.")
    return data_rows

def tool_total_clients_online(make_pdf=True):
    if make_pdf: print("\nCounting Total Clients currently connected...")
    total_clients = 0
    try:
        networks = dashboard.organizations.getOrganizationNetworks(ORG_ID, total_pages='all')
        if make_pdf: print(f"Discovered {len(networks)} networks. Fetching live client counts...")
        
        for i, net in enumerate(networks, 1):
            if make_pdf: print(f"Scanning network {i}/{len(networks)}: {net.get('name', 'Unknown')[:35]}")
            
            if 'wireless' in net.get('productTypes', []) or 'switch' in net.get('productTypes', []):
                try:
                    clients = dashboard.networks.getNetworkClients(net['id'], timespan=86400, statuses=['Online'], total_pages='all')
                    total_clients += len(clients)
                except meraki.APIError:
                    pass 
                    
        if make_pdf:
            print(f"\n[+] RESULT: {total_clients:,} Total Clients Currently Connected")
            generate_pdf_report("Total Clients Connected to Organization", ['Metric', 'Count'], [135, 135], [['Total Online Clients', str(total_clients)]], "Report_Total_Clients_Connected.pdf")
    except Exception as e:
        if make_pdf: print(f"\n[!] Error getting client totals: {e}")
    return total_clients

def tool_total_aps_online(make_pdf=True):
    if make_pdf: print("\nCounting Total APs Online...")
    devices = dashboard.organizations.getOrganizationDevicesStatuses(ORG_ID, productTypes=['wireless'], total_pages='all')
    online_count = sum(1 for dev in devices if dev.get('status', '').lower() == 'online')
    if make_pdf:
        print(f"\n[+] RESULT: {online_count:,} APs Online")
        generate_pdf_report("Total APs Online", ['Metric', 'Count'], [135, 135], [['Total Online APs', str(online_count)]], "Report_Total_APs_Online.pdf")
    return online_count

def tool_total_switches_online(make_pdf=True):
    if make_pdf: print("\nCounting Total Switches Online...")
    devices = dashboard.organizations.getOrganizationDevicesStatuses(ORG_ID, productTypes=['switch'], total_pages='all')
    online_count = sum(1 for dev in devices if dev.get('status', '').lower() == 'online')
    if make_pdf:
        print(f"\n[+] RESULT: {online_count:,} Switches Online")
        generate_pdf_report("Total Switches Online", ['Metric', 'Count'], [135, 135], [['Total Online Switches', str(online_count)]], "Report_Total_Switches_Online.pdf")
    return online_count

def tool_total_cameras_online(make_pdf=True):
    if make_pdf: print("\nCounting Total Cameras Online...")
    devices = dashboard.organizations.getOrganizationDevicesStatuses(ORG_ID, productTypes=['camera'], total_pages='all')
    online_count = sum(1 for dev in devices if dev.get('status', '').lower() == 'online')
    if make_pdf:
        print(f"\n[+] RESULT: {online_count:,} Cameras Online")
        generate_pdf_report("Total Cameras Online", ['Metric', 'Count'], [135, 135], [['Total Online Cameras', str(online_count)]], "Report_Total_Cameras_Online.pdf")
    return online_count

def tool_total_sensors_online(make_pdf=True):
    if make_pdf: print("\nCounting Total Sensors Online...")
    devices = dashboard.organizations.getOrganizationDevicesStatuses(ORG_ID, productTypes=['sensor'], total_pages='all')
    online_count = sum(1 for dev in devices if dev.get('status', '').lower() == 'online')
    if make_pdf:
        print(f"\n[+] RESULT: {online_count:,} Sensors Online")
        generate_pdf_report("Total Sensors Online", ['Metric', 'Count'], [135, 135], [['Total Online Sensors', str(online_count)]], "Report_Total_Sensors_Online.pdf")
    return online_count

def tool_ap_statuses(status_filter, make_pdf=True):
    if make_pdf: print(f"\nScanning for {status_filter} APs...")
    data_rows = []
    devices = dashboard.organizations.getOrganizationDevicesStatuses(ORG_ID, productTypes=['wireless'], total_pages='all')
    
    for dev in devices:
        dev_status = dev.get('status', '').lower()
        dev_name = dev.get('name', dev.get('mac', 'Unnamed AP'))
        is_offline_type = status_filter == 'offline' and dev_status in ['offline', 'alerting']
        
        if is_offline_type:
            lan_ip = dev.get('lanIp', 'N/A (Repeater/Offline)')
            data_rows.append([dev_name, dev_status.capitalize(), lan_ip, dev.get('networkId', 'Unknown')])

    if make_pdf:
        title = "Total APs Alerting, Offline or Repeater"
        if data_rows:
            print(f"\n[+] Found {len(data_rows)} offline/repeater APs:")
            for r in data_rows:
                print(f"  - {r[0]} (Status: {r[1]}) -> IP: {r[2]}")
            generate_pdf_report(title, ['AP Name', 'Status', 'LAN IP', 'Network ID'], [80, 40, 60, 90], data_rows, f"Report_{title.replace(' ', '_')}.pdf")
        else:
            print(f"\n[+] Good news! No APs found matching status: {status_filter}.")
    return data_rows

def tool_existing_networks(make_pdf=True):
    if make_pdf: print("\nGathering existing networks...")
    data_rows = []
    networks = dashboard.organizations.getOrganizationNetworks(ORG_ID, total_pages='all')
    
    for net in networks:
        net_name = net.get('name', 'Unknown')
        net_id = net.get('id', 'Unknown')
        time_zone = net.get('timeZone', 'Unknown')
        tags = ", ".join(net.get('tags', [])) if net.get('tags') else "None"
        data_rows.append([net_name, net_id, time_zone, tags])
        
    if make_pdf:
        if data_rows:
            print(f"\n[+] Found {len(data_rows)} Total Networks:")
            for r in data_rows[:10]: # Print top 10 to keep console clean
                print(f"  - {r[0]} (ID: {r[1]})")
            if len(data_rows) > 10: print(f"  ... and {len(data_rows)-10} more.")
            generate_pdf_report("Existing Meraki Networks", ['Network Name', 'Network ID', 'Time Zone', 'Tags'], [80, 50, 70, 70], data_rows, "Report_Existing_Networks.pdf")
        else:
            print("\n[!] No networks found in this organization.")
    return data_rows

def tool_aps_down_today(make_pdf=True):
    if make_pdf: print("\nScanning for APs reported down today...")
    data_rows = []
    devices = dashboard.organizations.getOrganizationDevicesStatuses(ORG_ID, productTypes=['wireless'], total_pages='all')
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    for dev in devices:
        status = dev.get('status', '').lower()
        if status in ['offline', 'alerting']:
            last_reported = dev.get('lastReportedAt', '')
            if last_reported.startswith(today_str):
                dev_name = dev.get('name', dev.get('mac', 'Unnamed AP'))
                net_id = dev.get('networkId', 'Unknown')
                data_rows.append([dev_name, net_id, status.capitalize(), last_reported])

    if make_pdf:
        if data_rows:
            print(f"\n[+] CRITICAL: Found {len(data_rows)} APs down today:")
            for r in data_rows:
                print(f"  - {r[0]} reported {r[2]} at {r[3]}")
            generate_pdf_report("APs Reported Down Today", ['AP Name', 'Network ID', 'Status', 'Last Reported Time'], [70, 60, 40, 100], data_rows, "Report_APs_Down_Today.pdf")
        else:
            print("\n[+] Good news! No APs have dropped offline today.")
    return data_rows

# ----------------------------
# Corporate Daily Report Generation
# ----------------------------
class CorporateReportPDF(FPDF):
    def header(self):
        self.set_fill_color(41, 128, 185) 
        self.rect(0, 0, 297, 20, 'F')
        self.set_y(6)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'Meraki Network Health | Executive Summary by Ramon Solis', border=0, ln=1, align='C')
        self.set_text_color(0, 0, 0) 
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
    def add_table(self, title, headers, col_widths, data_rows):
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, title, ln=True)
        self.set_font("Arial", 'B', 10)
        self.set_fill_color(41, 128, 185) 
        self.set_text_color(255, 255, 255) 
        for i in range(len(headers)):
            self.cell(col_widths[i], 10, headers[i], border=1, align='C', fill=True)
        self.ln()
        self.set_font("Arial", '', 10)
        self.set_text_color(0, 0, 0)
        for row in data_rows:
            for i in range(len(row)):
                self.cell(col_widths[i], 10, str(row[i])[:45], border=1)
            self.ln()
        self.ln(10) 

def tool_daily_report():
    print("\n=== GENERATING UNIFIED CORPORATE DAILY REPORT ===")
    print("Gathering data across all endpoints. Please wait...\n")
    
    print("[1/9] Counting Total Clients...")
    total_clients = tool_total_clients_online(make_pdf=False)
    
    print("[2/9] Counting Online APs...")
    aps_online = tool_total_aps_online(make_pdf=False)
    
    print("[3/9] Counting Switches...")
    switches_online = tool_total_switches_online(make_pdf=False)
    sw_devices = dashboard.organizations.getOrganizationDevicesStatuses(ORG_ID, productTypes=['switch'], total_pages='all')
    switches_offline = sum(1 for dev in sw_devices if dev.get('status', '').lower() in ['offline', 'alerting'])

    print("[4/9] Counting Cameras...")
    cameras_online = tool_total_cameras_online(make_pdf=False)
    cam_devices = dashboard.organizations.getOrganizationDevicesStatuses(ORG_ID, productTypes=['camera'], total_pages='all')
    cameras_offline = sum(1 for dev in cam_devices if dev.get('status', '').lower() in ['offline', 'alerting'])

    print("[5/9] Counting Sensors...")
    sensors_online = tool_total_sensors_online(make_pdf=False)
    sensor_devices = dashboard.organizations.getOrganizationDevicesStatuses(ORG_ID, productTypes=['sensor'], total_pages='all')
    sensors_offline = sum(1 for dev in sensor_devices if dev.get('status', '').lower() in ['offline', 'alerting'])
    
    print("[6/9] Finding Offline APs...")
    offline_aps_data = tool_ap_statuses('offline', make_pdf=False)
    total_offline_aps = len(offline_aps_data)
    
    print("[7/9] Checking APs down today...")
    aps_down_today_data = tool_aps_down_today(make_pdf=False)
    
    print("[8/9] Fetching existing networks...")
    networks_data = tool_existing_networks(make_pdf=False)
    
    print("[9/9] Checking AP port speeds...")
    slow_aps_data = tool_slow_aps(make_pdf=False)
    total_slow_aps = len(slow_aps_data)
    
    print("\nData collection complete! Generating PDF and Charts...")

    fig, ax = plt.subplots(figsize=(20, 5), facecolor='white')
    ax.axis('off')
    
    color_up, color_down, color_border = '#28a745', '#dc3545', '#00AEEF'
    
    bw, bh = 1.4, 2.0 
    gap = 0.1 
    group_width = (bw * 2) + gap 
    spacing = 0.7 
    
    ax.add_patch(plt.Rectangle((-0.4, -0.6), 14.8, 3.5, fill=False, edgecolor=color_border, linewidth=3))
    
    def draw_blocks(start_x, val_up, val_down, title):
        ax.add_patch(plt.Rectangle((start_x, 0), bw, bh, facecolor=color_up, edgecolor='black', linewidth=3))
        ax.add_patch(plt.Rectangle((start_x + bw + gap, 0), bw, bh, facecolor=color_down, edgecolor='black', linewidth=3))
        
        ax.text(start_x + (bw/2), bh/2, str(val_up), ha='center', va='center', fontsize=36, fontweight='bold', color='black')
        ax.text(start_x + bw + gap + (bw/2), bh/2, str(val_down), ha='center', va='center', fontsize=36, fontweight='bold', color='black')
        
        ax.text(start_x + (bw/2), bh + 0.15, "UP", ha='center', va='bottom', fontsize=24, fontweight='bold')
        ax.text(start_x + bw + gap + (bw/2), bh + 0.15, "DOWN", ha='center', va='bottom', fontsize=24, fontweight='bold')
        
        ax.text(start_x + (group_width/2), -0.2, title, ha='center', va='top', fontsize=18, fontweight='bold')

    pos1 = 0.0
    pos2 = pos1 + group_width + spacing
    pos3 = pos2 + group_width + spacing
    pos4 = pos3 + group_width + spacing

    draw_blocks(pos1, aps_online, total_offline_aps, "Meraki Access Points")
    draw_blocks(pos2, switches_online, switches_offline, "Meraki Switches")
    draw_blocks(pos3, cameras_online, cameras_offline, "Meraki Cameras")
    draw_blocks(pos4, sensors_online, sensors_offline, "Meraki Sensors")

    ax.set_xlim(-0.5, 14.5)
    ax.set_ylim(-0.8, 2.9)

    chart_filename = 'temp_ap_chart.png'
    plt.savefig(chart_filename, bbox_inches='tight', facecolor=fig.get_facecolor(), dpi=200)
    plt.close()

    pdf = CorporateReportPDF(orientation='L')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')} | Time: {datetime.now().strftime('%H:%M')}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 14)
    pdf.cell(0, 8, f"Total Networks in Organization: {len(networks_data)}", ln=True)
    pdf.cell(0, 8, f"Grand Total Active Clients: {total_clients:,}", ln=True)
    pdf.cell(0, 8, f"Total Access Points Online: {aps_online:,}", ln=True)
    pdf.cell(0, 8, f"Total Meraki Switches Online: {switches_online:,}", ln=True) 
    pdf.cell(0, 8, f"Total Meraki Cameras Online: {cameras_online:,}", ln=True) 
    pdf.cell(0, 8, f"Total Meraki Sensors Online: {sensors_online:,}", ln=True) 
    pdf.cell(0, 8, f"Total Access Points with Issues: {total_offline_aps:,}", ln=True)
    pdf.cell(0, 8, f"Total Access Points running at 100 Mbps: {total_slow_aps:,}", ln=True)
    
    pdf.image(chart_filename, x=105, y=30, w=185) 
    pdf.set_y(100) 
    
    if aps_down_today_data:
        pdf.add_table("CRITICAL: APs Reported Down TODAY", ['AP Name', 'Network ID', 'Status', 'Last Reported'], [70, 60, 40, 100], aps_down_today_data)
    if offline_aps_data:
        pdf.add_table("All Current Offline / Repeater APs", ['AP Name', 'Status', 'LAN IP', 'Network ID'], [80, 40, 60, 90], offline_aps_data)
    if slow_aps_data:
        pdf.add_table("Meraki APs Running Below 1 Gbps", ['AP Name', 'Current Speed', 'Upstream Switch', 'Switch Port'], [80, 40, 90, 60], slow_aps_data)
    if networks_data:
        pdf.add_page() 
        pdf.add_table("Existing School Networks Dashboard", ['Network Name', 'Network ID', 'Time Zone', 'Tags'], [80, 50, 70, 70], networks_data)

    final_filename = f"Executive_Daily_Report_{datetime.now().strftime('%Y_%m_%d')}.pdf"
    pdf.output(final_filename)
    if os.path.exists(chart_filename):
        os.remove(chart_filename)

    print(f"\n[+] Corporate Daily Report successfully saved to: {final_filename}")

# ----------------------------
# GUI Implementations
# ----------------------------
class PrintLogger:
    """Redirects console print statements to the Tkinter Text widget."""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)

    def flush(self):
        pass

def run_task(target_function, *args):
    """Runs a function in a separate thread so the GUI doesn't freeze."""
    def wrapper():
        try:
            target_function(*args)
            print("\n--- Task Completed Successfully ---")
        except Exception as e:
            print(f"\n[!] Error during task: {e}")
    
    threading.Thread(target=wrapper, daemon=True).start()

def secure_exit(window, text_widget=None):
    """Securely flushes sensitive variables from memory before closing."""
    global dashboard, ORG_ID
    
    if text_widget:
        text_widget.delete('1.0', tk.END)
    
    try:
        del dashboard
        del ORG_ID
        if "MERAKI_API_KEY" in os.environ:
            del os.environ["MERAKI_API_KEY"]
    except NameError:
        pass 
        
    gc.collect()
    
    print("Memory flushed. Exiting securely...")
    window.destroy()
    sys.exit(0)

def open_main_menu(root_window=None):
    if root_window:
        root_window.destroy() 
    
    menu_window = tk.Tk()
    menu_window.title("Meraki Dashboard Tools | by Ramon Solis © 2026")
    menu_window.geometry("800x700")
    menu_window.configure(bg="#f4f4f4")

    # Header
    header = tk.Label(menu_window, text="Meraki Network Tools", font=("Arial", 18, "bold"), bg="#2980b9", fg="white", pady=10)
    header.pack(fill=tk.X)

    # Frame for Buttons
    btn_frame = tk.Frame(menu_window, bg="#f4f4f4")
    btn_frame.pack(pady=20)

    # Styling for Buttons
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 10), padding=5)

    buttons = [
        ("1) Show APs running at 100 Mbps", tool_slow_aps),
        ("2) Show Total Clients Currently Connected", tool_total_clients_online),
        ("3) Show Total APs Online", tool_total_aps_online),
        ("4) Show Total Switches Online", tool_total_switches_online),
        ("5) Show Total Cameras Online", tool_total_cameras_online),
        ("6) Show Total Sensors Online", tool_total_sensors_online),
        ("7) Show Alerting/Offline APs", lambda: tool_ap_statuses('offline')),
        ("8) Show Existing School Networks", tool_existing_networks),
        ("9) Show APs Reported Down Today", tool_aps_down_today),
        ("10) Generate Executive Daily Report (PDF)", tool_daily_report)
    ]

    for i, (text, func) in enumerate(buttons):
        row = i // 2
        col = i % 2
        btn = ttk.Button(btn_frame, text=text, width=45, command=lambda f=func: run_task(f))
        btn.grid(row=row, column=col, padx=10, pady=5)

    console_label = tk.Label(menu_window, text="Live Output Status:", font=("Arial", 10, "bold"), bg="#f4f4f4")
    console_label.pack(anchor="w", padx=20)

    console_text = tk.Text(menu_window, height=15, bg="black", fg="#00ff00", font=("Consolas", 10))
    console_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

    exit_btn = ttk.Button(menu_window, text="Secure Exit Application", width=45, command=lambda: secure_exit(menu_window, console_text))
    exit_btn.pack(pady=5)
    
    menu_window.protocol("WM_DELETE_WINDOW", lambda: secure_exit(menu_window, console_text))

    sys.stdout = PrintLogger(console_text)

    menu_window.mainloop()

def perform_manual_login(login_window, api_entry, org_entry):
    global dashboard, ORG_ID
    
    entered_api = api_entry.get().strip()
    entered_org = org_entry.get().strip()

    if not entered_api or not entered_org:
        messagebox.showwarning("Input Error", "Please enter both the API Key and Organization ID.")
        return

    try:
        test_dash = meraki.DashboardAPI(entered_api, suppress_logging=True, print_console=False)
        test_dash.organizations.getOrganization(entered_org)
        
        dashboard = test_dash
        ORG_ID = entered_org
        open_main_menu(login_window)

    except meraki.APIError as e:
        messagebox.showerror("Authentication Failed", f"Invalid API Key or Organization ID.\n\nDetails: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")

def create_login_window():
    login_window = tk.Tk()
    login_window.title("Meraki Login Tool | Ramon Solis © 2026")
    login_window.geometry("400x250")
    login_window.configure(bg="#2c3e50")

    login_window.update_idletasks()
    x = (login_window.winfo_screenwidth() // 2) - (400 // 2)
    y = (login_window.winfo_screenheight() // 2) - (250 // 2)
    login_window.geometry(f"+{x}+{y}")

    title_label = tk.Label(login_window, text="Meraki API Key & Org. ID", font=("Arial", 16, "bold"), bg="#2c3e50", fg="white")
    title_label.pack(pady=15)

    api_frame = tk.Frame(login_window, bg="#2c3e50")
    api_frame.pack(pady=5)
    tk.Label(api_frame, text="API Key:", font=("Arial", 10, "bold"), bg="#2c3e50", fg="white", width=10, anchor="e").pack(side=tk.LEFT, padx=5)
    api_entry = tk.Entry(api_frame, width=30, show="*")
    api_entry.pack(side=tk.LEFT)

    org_frame = tk.Frame(login_window, bg="#2c3e50")
    org_frame.pack(pady=5)
    tk.Label(org_frame, text="Org. ID:", font=("Arial", 10, "bold"), bg="#2c3e50", fg="white", width=10, anchor="e").pack(side=tk.LEFT, padx=5)
    org_entry = tk.Entry(org_frame, width=30)
    org_entry.insert(0, "") # PRE-FILLED WITH NEW NUMBER
    org_entry.pack(side=tk.LEFT)

    login_btn = tk.Button(login_window, text="Authenticate", font=("Arial", 10, "bold"), bg="#27ae60", fg="white", command=lambda: perform_manual_login(login_window, api_entry, org_entry))
    login_btn.pack(pady=20)

    login_window.bind('<Return>', lambda event: perform_manual_login(login_window, api_entry, org_entry))
    login_window.protocol("WM_DELETE_WINDOW", lambda: secure_exit(login_window))

    login_window.mainloop()

def attempt_auto_login():
    """Checks for .env credentials and attempts to silently login."""
    global dashboard, ORG_ID
    load_dotenv()
    
    env_api = os.getenv("MERAKI_API_KEY")
    env_org = os.getenv("MERAKI_ORG_ID")

    if env_api and env_org:
        try:
            test_dash = meraki.DashboardAPI(env_api, suppress_logging=True, print_console=False)
            test_dash.organizations.getOrganization(env_org)
            
            dashboard = test_dash
            ORG_ID = env_org
            return True
        except Exception:
            return False
    return False

# --- NEW SPLASH SCREEN LOGIC ---
def create_splash_screen():
    splash = tk.Tk()
    
    splash_width = 500
    splash_height = 250
    splash.update_idletasks()
    x = (splash.winfo_screenwidth() // 2) - (splash_width // 2)
    y = (splash.winfo_screenheight() // 2) - (splash_height // 2)
    splash.geometry(f"{splash_width}x{splash_height}+{x}+{y}")
    
    splash.overrideredirect(True)
    
    border_frame = tk.Frame(splash, bg="white", highlightbackground="black", highlightthickness=4)
    border_frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(border_frame, text="Welcome to Meraki Dashboard API Tool", font=("Arial", 16, "bold"), bg="white").pack(pady=(20, 10))
    tk.Label(border_frame, text="Searching for API & Org ID: .env File", font=("Arial", 14), bg="white").pack(pady=5)

    style = ttk.Style()
    style.theme_use('clam') 
    style.configure("Green.Horizontal.TProgressbar", foreground='green', background='green')
    
    progress = ttk.Progressbar(border_frame, style="Green.Horizontal.TProgressbar", orient=tk.HORIZONTAL, length=300, mode='determinate')
    progress.pack(pady=20)

    result_label = tk.Label(border_frame, text="", font=("Arial", 14, "bold"), bg="white")
    result_label.pack(pady=10)

    def run_check():
        time.sleep(1.0)
        success = attempt_auto_login()
        splash.after(0, lambda: finish_splash(success))

    def finish_splash(success):
        progress.stop()
        progress['value'] = 100 
        
        if success:
            result_label.config(text="API & Org ID founded | Access Granted", fg="green")
            splash.after(1500, lambda: open_main_menu(splash))
        else:
            result_label.config(text="Please enter your API key and Meraki Organization ID\non the following screen.", fg="red", font=("Arial", 11, "bold"))
            # EXACTLY 5 SECONDS DELAY
            splash.after(5000, lambda: [splash.destroy(), create_login_window()])

    progress.start(15)
    threading.Thread(target=run_check, daemon=True).start()

    splash.mainloop()

# ----------------------------
# Main Execution Flow
# ----------------------------
if __name__ == "__main__":
    create_splash_screen()
