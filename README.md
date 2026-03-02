# Meraki_Dashboard_API_Tools
# 🌐 Meraki Dashboard Tools (GUI Edition)

**Author:** Ramon Solis  
**Date:** February 2026  

## 📌 Overview
The **Meraki Dashboard Tools API** is a secure, graphical desktop application designed to interface directly with the Cisco Meraki Cloud API. Built for network administrators, this tool provides real-time insights into the health of enterprise networks. 

It features a threaded graphical user interface (GUI) built with `tkinter`, an auto-dependency installer with UAC elevation, Multi-Factor Authentication (MFA) via TOTP, secure memory management, and automated generation of corporate-styled PDF Executive Summaries.

---

## ✨ Key Features
* **Auto-Dependency Installer:** Automatically checks for required Python modules upon launch. If missing, it requests administrative elevation (via UAC) and installs them natively.
* **Animated Splash Screen:** Initiates an automated, secure background check for stored credentials before launching.
* **Multi-Factor Authentication (MFA):** Integrates standard Time-based One-Time Passwords (TOTP) compatible with Google Authenticator, Microsoft Authenticator, and Duo.
* **Hybrid Authentication:** Supports both zero-touch `.env` automated logins and a secure manual login fallback with password masking.
* **Live Console Output:** Real-time terminal output is routed directly into the GUI without freezing the application, utilizing background threading.
* **Automated PDF Reporting:** Uses `fpdf2` and `matplotlib` to generate visually appealing network health reports and graphical dashboards.
* **Secure Memory Flush:** Integrates Python's Garbage Collector (`gc`) to securely wipe sensitive variables (like API keys) from physical RAM upon exit.

---

## ⚙️ Prerequisites & Setup

### 1. Required Software
Ensure you have **Python 3.8+** installed on your system.

### 2. Dependencies (Automated)
The script includes an auto-installer block at the header. It will automatically attempt to install the following if they are missing:
* `meraki`
* `fpdf2`
* `matplotlib`
* `python-dotenv`
* `pyotp`

### 3. Meraki API Key
You must have a valid Cisco Meraki API Key. For security purposes, it is highly recommended to generate this key from an account that possesses **Read-Only** access to the Meraki Organization.

---

## 🔐 Authentication & MFA Guide

This application prevents the dangerous practice of hardcoding secret keys into the source code by utilizing a hidden configuration file and enforcing MFA.

### Method A: Automated Silent Login (Recommended)
For seamless daily use without typing your credentials every time, create a local environment file.
1. In the same directory as the script, create a plain text file named exactly `.env`.
2. Add the following lines, replacing the placeholder with your actual API key:
   ```text
   MERAKI_API_KEY=your_actual_api_key_here
   MERAKI_ORG_ID=1234567

   
**** Main Menu Options  ****
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
