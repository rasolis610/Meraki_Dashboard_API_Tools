# Meraki_Dashboard_API_Tools
The **Meraki Dashboard Tools API** is a secure, graphical desktop application designed to interface directly with the Cisco Meraki Cloud API. Built for network administrators, this tool provides real-time insights into the health of enterprise networks.
Meraki Dashboard Tools (GUI Edition)
Overview
The Meraki Dashboard Tools application is a secure, graphical desktop tool designed to interface directly with the Cisco Meraki Cloud API. It provides network administrators with real-time insights into the health of their enterprise network, specifically tailored for Paterson Public Schools.

The tool generates instant, on-screen console readouts as well as highly polished, corporate-styled PDF Executive Summaries featuring custom UP/DOWN health graphics for Access Points, Switches, Cameras, and Sensors.
1. Prerequisites & Setup
Required Software
• Python 3.8+ installed on your system.
• Required Python Libraries: meraki, fpdf, matplotlib, python-dotenv
Install the  Library>>>>> pip install meraki fpdf2 matplotlib python-dotenv
API Requirements
You must have a valid Cisco Meraki API Key generated from an account with at least "Read-Only" organization access.
3. Authentication & The .env File
This application utilizes a hybrid, highly secure authentication model to prevent hardcoding secret keys.
Method A: Automatic Silent Login
1. Create a plain text file named exactly .env in the same folder as the script.
2. Add MERAKI_API_KEY=your_key and MERAKI_ORG_ID=your_org_id.
3. When you open the app, it will instantly securely authenticate in the background.
Method B: Manual GUI Login
If the .env file is missing, the app gracefully falls back to a Secure Login Window with masked inputs to prevent shoulder-surfing.
3. Main Menu Options
1. Show APs running at 100 Mbps: Identifies any AP running slower than 1 Gbps.
2. Show Total Clients Currently Connected: Pulls a live count of active clients.
3. Show Total APs Online: Counts all Online Access Points.
4. Show Total Switches Online: Counts all Online Meraki Switches.
5. Show Total Cameras Online: Counts all Online Meraki MV Cameras.
6. Show Total Sensors Online: Counts all Online Meraki MT Sensors.
7. Show Alerting/Offline APs: Scans for APs experiencing outages.
8. Show Existing School Networks: Lists all configured network sites.
9. Show APs Reported Down Today: Highlights APs that specifically dropped offline today.
10. Generate Executive Daily Report (PDF): Aggregates all data into a corporate-branded PDF.
4. Compiling to a Standalone Executable (.exe)
To share this application without requiring Python installation, compile it using PyInstaller:
pyinstaller --noconsole --onefile your_script_name.py
