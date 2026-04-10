from tkinter import *
import pickle as p
import tkinter.messagebox
import csv
from tkinter import ttk
import datetime
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from tkcalendar import *
import customtkinter
from PIL import ImageTk, Image
from customtkinter import CTkImage
import ctypes
import os
import subprocess
import matplotlib
matplotlib.use("TkAgg")
import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
# THEME
customtkinter.set_appearance_mode("light")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green
#TO NEXT WIDGET
def go_to_next_element(event):
    event.widget.tk_focusNext().focus()

def load_dashboard_data():
    """Load real data from CSV files for dashboard"""
    base_path = "/Users/apple/Desktop/2nd year/Python Project sem 3/"
    
    # Find last usage date (most recent entry date from stentused.csv)
    last_usage_date = None
    today = datetime.now().strftime("%Y-%m-%d")
    today_formats = [
        today,  # YYYY-MM-DD
        datetime.now().strftime("%d/%m/%Y"),  # DD/MM/YYYY
        datetime.now().strftime("%m/%d/%Y")   # MM/DD/YYYY
    ]
    
    hospital_counts = {}  # For all-time usage (bar chart on left) - from used stents only
    hospital_today_counts = {}  # For today's usage
    expiry_counts = {}
    
    try:
        # Read used stents from stentused.csv
        f = open(f"{base_path}stentused.csv", "r", errors="ignore")
        reader = csv.reader(f)
        for row in reader:
            if row and len(row) >= 13:
                # Used stent entry format: [Doctor, Hospital, Patient, Bill Amt, IPD, Cath, Bill No, Stent Type, Size, Batch, Serial, Entry, Expiry]
                hospital = row[1].strip() if len(row) > 1 and row[1] else "Unknown"
                if not hospital or hospital == "":
                    hospital = "Unknown"
                
                # All-time counts (all used stents)
                if hospital not in hospital_counts:
                    hospital_counts[hospital] = 0
                hospital_counts[hospital] += 1
                
                # Check entry date at index 11 for last usage date
                if len(row) > 11:
                    entry_date_str = str(row[11]).strip()
                    # Try to parse date and find most recent
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                        try:
                            entry_date = datetime.strptime(entry_date_str, fmt)
                            if last_usage_date is None or entry_date > last_usage_date:
                                last_usage_date = entry_date
                            break
                        except:
                            continue
                    
                    # Check if used today
                    is_today = False
                    for date_format in today_formats:
                        if entry_date_str == date_format:
                            is_today = True
                            break
                    
                    if is_today:
                        if hospital not in hospital_today_counts:
                            hospital_today_counts[hospital] = 0
                        hospital_today_counts[hospital] += 1
        f.close()
    except FileNotFoundError:
        # File doesn't exist yet, that's okay
        pass
    except Exception as e:
        print(f"Error reading stentused.csv: {e}")
        pass
    
    # Note: hospital_counts now only includes used stents, not hospital stock
    # Hospital stock is separate inventory, not usage data
    
    # Find earliest expiry date (from officestock.csv and hospitalstock.csv)
    earliest_expiry_date = None
    expiring_soon = 0
    
    try:
        # Check officestock.csv
        f = open(f"{base_path}officestock.csv", "r", errors="ignore")
        reader = csv.reader(f)
        for row in reader:
            if row and len(row) > 5:
                try:
                    expiry_str = row[5]
                    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
                    days_until = (expiry_date - datetime.now()).days
                    if 0 <= days_until <= 30:
                        expiring_soon += 1
                    # Track earliest expiry date
                    if earliest_expiry_date is None or expiry_date < earliest_expiry_date:
                        earliest_expiry_date = expiry_date
                    month = expiry_date.strftime("%B")
                    expiry_counts[month] = expiry_counts.get(month, 0) + 1
                except:
                    pass
        f.close()
    except:
        pass
    
    try:
        # Check hospitalstock.csv
        f = open(f"{base_path}hospitalstock.csv", "r", errors="ignore")
        reader = csv.reader(f)
        for row in reader:
            if row and len(row) > 6:
                try:
                    expiry_str = row[6]
                    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
                    days_until = (expiry_date - datetime.now()).days
                    if 0 <= days_until <= 30:
                        expiring_soon += 1
                    # Track earliest expiry date
                    if earliest_expiry_date is None or expiry_date < earliest_expiry_date:
                        earliest_expiry_date = expiry_date
                except:
                    pass
        f.close()
    except:
        pass
    
    # Create hospital DataFrame (all-time usage) - include ALL hospitals, not just first 4
    if not hospital_counts:
        # If no data, create empty DataFrame with proper structure
        hospitals_df = pd.DataFrame({
            "Hospital": [],
            "Stents Used": []
        })
    else:
        hospitals_df = pd.DataFrame({
            "Hospital": list(hospital_counts.keys()),
            "Stents Used": list(hospital_counts.values())
        })
        # Sort by usage descending
        hospitals_df = hospitals_df.sort_values("Stents Used", ascending=False)
    
    # Create today's usage DataFrame for the graph
    if not hospital_today_counts:
        hospital_today_counts = {"Apollo": 0, "AIIMS": 0, "Fortis": 0, "Medanta": 0}
    
    today_df = pd.DataFrame({
        "Hospital": list(hospital_today_counts.keys()),
        "Stents Used Today": list(hospital_today_counts.values())
    })
    
    # Create monthly expiry DataFrame (for reference, but we'll use today's graph instead)
    if not expiry_counts:
        expiry_counts = {"January": 23, "February": 18, "March": 31, "April": 15, "May": 12}
    
    total_expiry = sum(expiry_counts.values()) if expiry_counts.values() else 100
    monthly_data = []
    for month, count in expiry_counts.items():
        monthly_data.append({"Month": month, "Percent": count / total_expiry if total_expiry > 0 else 0.2})
    
    monthly_df = pd.DataFrame(monthly_data)
    if monthly_df.empty:
        monthly_df = pd.DataFrame({
            "Month": ["January", "February", "March", "April"],
            "Percent": [0.23, 0.18, 0.31, 0.28]
        })
    
    # Format dates for display
    if last_usage_date:
        last_usage_display = last_usage_date.strftime("%d/%m/%Y")
    else:
        last_usage_display = "No data"
    
    if earliest_expiry_date:
        earliest_expiry_display = earliest_expiry_date.strftime("%d/%m/%Y")
    else:
        earliest_expiry_display = "No data"
    
    return hospitals_df, today_df, last_usage_display, earliest_expiry_display

def HB():#HOME PAGE WITH SIDEBAR
    # Constants
    CONTENT_BG = "#f8f9fa"
    SIDEBAR_BG = "#2f3b52"
    
    # Global variables for sidebar navigation
    current_view = None
    content_frame = None
    is_loading = False  # Flag to prevent multiple simultaneous loads
    
    def show_dashboard():
        """Display dashboard with real data"""
        nonlocal current_view, is_loading
        if is_loading:
            return  # Prevent multiple simultaneous loads
        is_loading = True
        
        if current_view:
            current_view.destroy()
        
        # Load real data
        hospitals_df, today_df, last_usage_date, earliest_expiry_date = load_dashboard_data()
        is_loading = False
        
        # Create dashboard frame
        dashboard_frame = customtkinter.CTkFrame(content_frame, fg_color=CONTENT_BG)
        dashboard_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = customtkinter.CTkFrame(dashboard_frame, fg_color=CONTENT_BG)
        header_frame.pack(fill="x", pady=(20, 10), padx=20)
        
        title = customtkinter.CTkLabel(
            header_frame,
            text="Stent Inventory Dashboard",
            font=("Helvetica Neue", 26, "bold"),
            text_color="#1f2a44",
            anchor="w"
        )
        title.pack(side="left")
        
        def refresh_dashboard():
            show_dashboard()
        
        refresh_btn = customtkinter.CTkButton(
            header_frame,
            text="↻ Refresh Data",
            font=("Helvetica Neue", 12, "bold"),
            fg_color="#4fa6f7",
            hover_color="#3c92e5",
            command=refresh_dashboard,
            width=150
        )
        refresh_btn.pack(side="right", padx=10)
        
        # Summary cards
        cards_frame = customtkinter.CTkFrame(dashboard_frame, fg_color=CONTENT_BG)
        cards_frame.pack(fill="x", padx=20, pady=10)
        
        # Card 1: Last Usage Date
        card1 = customtkinter.CTkFrame(cards_frame, fg_color="#8bbbf1", width=300, height=150)
        card1.pack(side="left", expand=True, fill="both", padx=(0, 10))
        
        card1_title = customtkinter.CTkLabel(card1, text="Last Usage Date", font=("Helvetica Neue", 18), text_color="#ffffff", anchor="w")
        card1_title.pack(anchor="nw", padx=20, pady=(15, 5))
        
        card1_value = customtkinter.CTkLabel(card1, text=last_usage_date, font=("Helvetica Neue", 28, "bold"), text_color="#ffffff")
        card1_value.pack(anchor="nw", padx=20)
        
        # Card 2: Earliest Expiry Date
        card2 = customtkinter.CTkFrame(cards_frame, fg_color="#f3d88b", width=300, height=150)
        card2.pack(side="left", expand=True, fill="both", padx=(10, 0))
        
        card2_title = customtkinter.CTkLabel(card2, text="Earliest Expiry Date", font=("Helvetica Neue", 18), text_color="#ffffff", anchor="w")
        card2_title.pack(anchor="nw", padx=20, pady=(15, 5))
        
        card2_value = customtkinter.CTkLabel(card2, text=earliest_expiry_date, font=("Helvetica Neue", 28, "bold"), text_color="#ffffff")
        card2_value.pack(anchor="nw", padx=20)
        
        # Charts frame (for top two charts side by side)
        charts_frame = customtkinter.CTkFrame(dashboard_frame, fg_color=CONTENT_BG)
        charts_frame.pack(fill="x", padx=20, pady=10)
        
        # Bar chart - Stents Used per Hospital (All-time)
        bar_container = customtkinter.CTkFrame(charts_frame, fg_color="#ffffff")
        bar_container.pack(side="left", expand=True, fill="both", padx=(0, 10))
        
        bar_title = customtkinter.CTkLabel(bar_container, text="Stents Used per Hospital (All-time)", font=("Helvetica Neue", 16, "bold"), text_color="#2f3b52", anchor="w")
        bar_title.pack(anchor="nw", padx=20, pady=(20, 10))
        
        fig_bar = Figure(figsize=(6, 4.5), dpi=100, facecolor='white')
        ax_bar = fig_bar.add_subplot(111)
        
        # Vibrant color palette for bars
        vibrant_colors = ['#FF8C00', '#1E3A8A', '#FF1493', '#800020', '#FF6B35', '#003366', '#FF69B4', '#8B0000', '#FFA500', '#000080']
        
        # Check if we have data
        if len(hospitals_df) > 0 and hospitals_df["Stents Used"].sum() > 0:
            # Filter out zero values and sort by value
            data = hospitals_df[hospitals_df["Stents Used"] > 0].sort_values("Stents Used", ascending=True)
            if len(data) > 0:
                labels = data["Hospital"].tolist()
                values = data["Stents Used"].tolist()
                colors = vibrant_colors[:len(labels)]
                
                # Create horizontal bar chart with better formatting
                bars = ax_bar.barh(labels, values, color=colors, edgecolor='white', linewidth=2, height=0.7)
                
                # Add value labels on bars
                if len(values) > 0:
                    max_val = max(values)
                    for i, (bar, val) in enumerate(zip(bars, values)):
                        width = bar.get_width()
                        ax_bar.text(width + max_val * 0.02, bar.get_y() + bar.get_height()/2, 
                                   f'{int(val)}', ha='left', va='center', fontweight='bold', fontsize=11, color='#1f2a44')
                
                # Format axes
                ax_bar.set_xlabel('Number of Stents', fontsize=13, fontweight='bold', color='#2f3b52', labelpad=10)
                ax_bar.set_ylabel('Hospital', fontsize=13, fontweight='bold', color='#2f3b52', labelpad=10)
                ax_bar.set_title('Distribution of Stent Usage', fontsize=15, fontweight='bold', pad=20, color='#1f2a44')
                
                # Improve grid and styling
                ax_bar.grid(axis='x', alpha=0.4, linestyle='--', linewidth=0.8, color='#d0d7e3')
                ax_bar.set_facecolor('#ffffff')
                ax_bar.spines['top'].set_visible(False)
                ax_bar.spines['right'].set_visible(False)
                ax_bar.spines['left'].set_color('#e0e7ef')
                ax_bar.spines['bottom'].set_color('#e0e7ef')
                ax_bar.tick_params(axis='x', colors='#64748b', labelsize=10)
                ax_bar.tick_params(axis='y', colors='#1f2a44', labelsize=10)
                
                # Set x-axis to start from 0 with better spacing
                ax_bar.set_xlim(0, max_val * 1.15)
            else:
                # Show empty graph with axes
                ax_bar.set_xlabel('Number of Stents', fontsize=13, fontweight='bold', color='#2f3b52', labelpad=10)
                ax_bar.set_ylabel('Hospital', fontsize=13, fontweight='bold', color='#2f3b52', labelpad=10)
                ax_bar.set_title('Distribution of Stent Usage', fontsize=15, fontweight='bold', pad=20, color='#1f2a44')
                ax_bar.set_xlim(0, 10)
                ax_bar.set_ylim(-0.5, 0.5)
                ax_bar.text(0.5, 0.5, 'No usage data available', 
                           ha='center', va='center', transform=ax_bar.transAxes,
                           fontsize=14, color="#94a3b8", fontweight='bold')
                ax_bar.grid(axis='x', alpha=0.4, linestyle='--', linewidth=0.8, color='#d0d7e3')
                ax_bar.set_facecolor('#ffffff')
                ax_bar.spines['top'].set_visible(False)
                ax_bar.spines['right'].set_visible(False)
        else:
            # Show empty graph with axes structure
            ax_bar.set_xlabel('Number of Stents', fontsize=13, fontweight='bold', color='#2f3b52', labelpad=10)
            ax_bar.set_ylabel('Hospital', fontsize=13, fontweight='bold', color='#2f3b52', labelpad=10)
            ax_bar.set_title('Distribution of Stent Usage', fontsize=15, fontweight='bold', pad=20, color='#1f2a44')
            ax_bar.set_xlim(0, 10)
            ax_bar.set_ylim(-0.5, 0.5)
            ax_bar.text(0.5, 0.5, 'No usage data available\nAdd used stent entries to see data', 
                       ha='center', va='center', transform=ax_bar.transAxes,
                       fontsize=12, color="#94a3b8", fontweight='bold')
            ax_bar.grid(axis='x', alpha=0.4, linestyle='--', linewidth=0.8, color='#d0d7e3')
            ax_bar.set_facecolor('#ffffff')
            ax_bar.spines['top'].set_visible(False)
            ax_bar.spines['right'].set_visible(False)
        
        fig_bar.tight_layout()
        
        bar_canvas = FigureCanvasTkAgg(fig_bar, master=bar_container)
        bar_canvas.draw()
        bar_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 20))
        
        # Line chart - Monthly Trend (Last 7 days or available data)
        line_container = customtkinter.CTkFrame(charts_frame, fg_color="#ffffff")
        line_container.pack(side="left", expand=True, fill="both", padx=(10, 0))
        
        # Replace "Stent Usage Trend" with "Insights: Top Stent Types by Usage"
        line_title = customtkinter.CTkLabel(line_container, text="📊 Insights: Top Stent Types by Usage", font=("Helvetica Neue", 16, "bold"), text_color="#2f3b52", anchor="w")
        line_title.pack(anchor="nw", padx=20, pady=(20, 10))
        
        fig_line = Figure(figsize=(6, 4.5), dpi=100, facecolor='white')
        ax_line = fig_line.add_subplot(111)
        
        # Collect stent type usage data (focus on actually used stents)
        try:
            base_path = "/Users/apple/Desktop/2nd year/Python Project sem 3/"
            stent_type_counts = {}
            
            # Read from stentused.csv - used stents data
            try:
                f = open(f"{base_path}stentused.csv", "r", errors="ignore")
                reader = csv.reader(f)
                for row in reader:
                    if row and len(row) >= 13:
                        # Used stent entry format: [Doctor, Hospital, Patient, Bill Amt, IPD, Cath, Bill No, Stent Type, Size, Batch, Serial, Entry, Expiry]
                        # Stent type is at index 7
                        stent_type = row[7].strip() if len(row) > 7 and row[7] else ""
                        if stent_type and stent_type.lower() != "unknown" and stent_type != "":
                            stent_type_counts[stent_type] = stent_type_counts.get(stent_type, 0) + 1
                f.close()
            except FileNotFoundError:
                # File doesn't exist yet
                pass
            except Exception as e:
                print(f"Error reading stentused.csv: {e}")
            
            # Filter and sort stent types
            if stent_type_counts:
                # Sort by count and get top 10 (ascending for better display)
                sorted_stents = sorted(stent_type_counts.items(), key=lambda x: x[1], reverse=False)[:10]
                stent_types = [item[0] for item in sorted_stents]
                counts = [item[1] for item in sorted_stents]
                
                # Better color palette - use Set3 with more vibrant colors
                insight_colors = plt.cm.Set3(np.linspace(0, 1, len(stent_types)))
                
                # Create horizontal bar chart with better formatting
                bars = ax_line.barh(stent_types, counts, color=insight_colors, edgecolor='white', linewidth=2, height=0.7)
                
                # Add value labels on bars
                if len(counts) > 0:
                    max_count = max(counts)
                    for i, (bar, val) in enumerate(zip(bars, counts)):
                        width = bar.get_width()
                        ax_line.text(width + max_count * 0.02, bar.get_y() + bar.get_height()/2, 
                                   f'{int(val)}', ha='left', va='center', fontweight='bold', fontsize=11, color='#1f2a44')
                
                # Format axes
                ax_line.set_xlabel('Number of Stents Used', fontsize=13, fontweight='bold', color='#2f3b52', labelpad=10)
                ax_line.set_ylabel('Stent Type', fontsize=13, fontweight='bold', color='#2f3b52', labelpad=10)
                ax_line.set_title('Distribution of Stent Types (All-time Usage)', fontsize=15, fontweight='bold', pad=20, color='#1f2a44')
                
                # Improve grid and styling
                ax_line.grid(axis='x', alpha=0.4, linestyle='--', linewidth=0.8, color='#d0d7e3')
                ax_line.set_facecolor('#ffffff')
                ax_line.spines['top'].set_visible(False)
                ax_line.spines['right'].set_visible(False)
                ax_line.spines['left'].set_color('#e0e7ef')
                ax_line.spines['bottom'].set_color('#e0e7ef')
                ax_line.tick_params(axis='x', colors='#64748b', labelsize=10)
                ax_line.tick_params(axis='y', colors='#1f2a44', labelsize=10)
                
                # Set x-axis to start from 0 with better spacing
                ax_line.set_xlim(0, max_count * 1.15)
                
                # Add total count annotation with better styling
                total_stents = sum(counts)
                ax_line.text(0.98, 0.02, f'Total: {total_stents} stents', 
                           transform=ax_line.transAxes, fontsize=11, 
                           fontweight='bold', ha='right', va='bottom',
                           bbox=dict(boxstyle='round,pad=0.5', facecolor='#fef3c7', 
                                   edgecolor='#f59e0b', linewidth=1.5, alpha=0.9),
                           color='#92400e')
            else:
                # Show empty graph with axes structure
                ax_line.set_xlabel('Number of Stents Used', fontsize=13, fontweight='bold', color='#2f3b52', labelpad=10)
                ax_line.set_ylabel('Stent Type', fontsize=13, fontweight='bold', color='#2f3b52', labelpad=10)
                ax_line.set_title('Distribution of Stent Types (All-time Usage)', fontsize=15, fontweight='bold', pad=20, color='#1f2a44')
                ax_line.set_xlim(0, 10)
                ax_line.set_ylim(-0.5, 0.5)
                ax_line.text(0.5, 0.5, 'No stent type data available\nAdd used stent entries to see insights', 
                           ha='center', va='center', transform=ax_line.transAxes,
                           fontsize=12, color="#94a3b8", fontweight='bold')
                ax_line.grid(axis='x', alpha=0.4, linestyle='--', linewidth=0.8, color='#d0d7e3')
                ax_line.set_facecolor('#ffffff')
                ax_line.spines['top'].set_visible(False)
                ax_line.spines['right'].set_visible(False)
        except Exception as e:
            ax_line.set_xlabel('Number of Stents Used', fontsize=13, fontweight='bold', color='#2f3b52', labelpad=10)
            ax_line.set_ylabel('Stent Type', fontsize=13, fontweight='bold', color='#2f3b52', labelpad=10)
            ax_line.set_title('Distribution of Stent Types (All-time Usage)', fontsize=15, fontweight='bold', pad=20, color='#1f2a44')
            ax_line.text(0.5, 0.5, f'Unable to load insight data\n{str(e)}', 
                       ha='center', va='center', transform=ax_line.transAxes,
                       fontsize=12, color="#94a3b8", fontweight='bold')
            ax_line.grid(axis='x', alpha=0.4, linestyle='--', linewidth=0.8, color='#d0d7e3')
            ax_line.set_facecolor('#ffffff')
            ax_line.spines['top'].set_visible(False)
            ax_line.spines['right'].set_visible(False)
        
        fig_line.tight_layout()
        
        line_canvas = FigureCanvasTkAgg(fig_line, master=line_container)
        line_canvas.draw()
        line_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 20))
        
        current_view = dashboard_frame
    
    def show_view(view_func=None):
        """Helper to show different views"""
        nonlocal current_view, is_loading
        if is_loading:
            return  # Prevent multiple simultaneous loads
        is_loading = True
        
        if current_view:
            try:
                current_view.destroy()
            except:
                pass
        if view_func:
            current_view = customtkinter.CTkFrame(content_frame)
            current_view.pack(fill="both", expand=True)
            view_func()
        is_loading = False
    
    def DE():#Data entry
        nonlocal current_view, is_loading
        if is_loading:
            return
        is_loading = True
        
        def homee():#HOME BUTTON
            nonlocal current_view, is_loading
            if current_view:
                try:
                    current_view.destroy()
                except:
                    pass
            is_loading = False
            show_dashboard()

        if current_view:
            try:
                current_view.destroy()
            except:
                pass
        
        root = customtkinter.CTkTabview(master=content_frame,height=600,width=1100)
        root.pack(fill="both", expand=True, padx=10, pady=10)
        current_view = root
        is_loading = False
        try:
            f = open("/Users/apple/Desktop/2nd year/Python Project sem 3/Dets.csv", "r", errors="ignore")
            r = csv.reader(f)
            Ho = []
            Do = []
            So = []
            for i in r:
                if i and len(i) > 0 and i[0] != "":
                    Ho.append(i[0].strip())
                if i and len(i) > 1 and i[1] != "":
                    Do.append(i[1].strip())
                if i and len(i) > 2 and i[2] != "":
                    So.append(i[2].strip())
            f.close()
            # Remove duplicates while preserving order
            Ho = list(dict.fromkeys(Ho))
            Do = list(dict.fromkeys(Do))
            So = list(dict.fromkeys(So))
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Failed to load dropdown data: {str(e)}")
            Ho = []
            Do = []
            So = []

        root1=root.add("Office")
        root2=root.add("Hospital")
        root3=root.add("Used")

        # Validation helper functions
        def check_serial_exists(serial_num, file_paths):
            """Check if serial number already exists in any file"""
            for file_path in file_paths:
                try:
                    f = open(file_path, "r", errors="ignore")
                    reader = csv.reader(f)
                    for row in reader:
                        if row:
                            # Check different column positions for serial number
                            if len(row) >= 4 and row[3] == serial_num:  # officestock.csv (office stock)
                                f.close()
                                return True
                            if len(row) >= 5 and row[4] == serial_num:  # hospitalstock.csv
                                f.close()
                                return True
                    f.close()
                except:
                    pass
            return False
        
        def check_serial_available_for_use(serial_num):
            """Check if serial number exists in available stock (office or hospital) and is not already used"""
            base_path = "/Users/apple/Desktop/2nd year/Python Project sem 3/"
            serial_found_in_stock = False
            serial_already_used = False
            
            # Check if serial exists in office stock (6 columns - not used)
            try:
                f = open(f"{base_path}officestock.csv", "r", errors="ignore")
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        # Office stock entry (6 columns, serial at index 3)
                        if len(row) == 6 and row[3] == serial_num:
                            serial_found_in_stock = True
                f.close()
            except:
                pass
            
            # Check if serial is already used (in stentused.csv)
            try:
                f = open(f"{base_path}stentused.csv", "r", errors="ignore")
                reader = csv.reader(f)
                for row in reader:
                    if row and len(row) >= 13 and row[10] == serial_num:  # Serial at index 10
                        serial_already_used = True
                f.close()
            except:
                pass
            
            # Check if serial exists in hospital stock (7 columns)
            try:
                f = open(f"{base_path}hospitalstock.csv", "r", errors="ignore")
                reader = csv.reader(f)
                for row in reader:
                    if row and len(row) >= 7 and row[4] == serial_num:
                        serial_found_in_stock = True
                f.close()
            except:
                pass
            
            return serial_found_in_stock, serial_already_used
        
        def validate_dates(entry_date, expiry_date):
            """Validate that expiry date is after entry date"""
            try:
                # Parse dates - handle different formats
                entry = datetime.strptime(str(entry_date), "%Y-%m-%d")
                expiry = datetime.strptime(str(expiry_date), "%Y-%m-%d")
                if expiry <= entry:
                    return False, "Expiry date must be after entry date"
                return True, ""
            except Exception as e:
                return False, f"Invalid date format: {str(e)}"
        
        def validate_numeric(value, field_name):
            """Validate numeric fields"""
            if not value or value.strip() == "":
                return False, f"{field_name} cannot be empty"
            try:
                float(value)
                return True, ""
            except:
                return False, f"{field_name} must be a valid number"
        
        def validate_required(value, field_name):
            """Validate required fields"""
            if not value or value.strip() == "":
                return False, f"{field_name} is required"
            return True, ""
        
        def highlight_field(entry_widget, is_valid=True):
            """Highlight field based on validation status"""
            if is_valid:
                entry_widget.configure(border_color="#d0d7e3", fg_color='#F8F1FF')
            else:
                entry_widget.configure(border_color="#ef4444", fg_color='#fee2e2')
        
        def validate_serial_realtime(serial_entry, file_paths):
            """Real-time validation for serial number"""
            serial = serial_entry.get().strip()
            if serial:
                if check_serial_exists(serial, file_paths):
                    highlight_field(serial_entry, False)
                    return False
                else:
                    highlight_field(serial_entry, True)
                    return True
            return None
        
        def validate_numeric_realtime(entry_widget, field_name=""):
            """Real-time validation for numeric fields"""
            value = entry_widget.get().strip()
            if value:
                try:
                    float(value)
                    if float(value) < 0:
                        highlight_field(entry_widget, False)
                        return False
                    highlight_field(entry_widget, True)
                    return True
                except:
                    highlight_field(entry_widget, False)
                    return False
            highlight_field(entry_widget, True)
            return None

        #OFFICE TAB
        def ent1():
            ST=sc1.get()
            SZ=e11.get().strip()
            BN=e21.get().strip()
            SN=e31.get().strip()
            ENT=str(cale.get_date())
            EXT=str(calx.get_date())
            
            # Validation
            errors = []
            
            # Validate required fields
            if not ST or ST.strip() == "":
                errors.append("Stent Type is required")
            if not validate_required(SZ, "Stent Size")[0]:
                errors.append(validate_required(SZ, "Stent Size")[1])
            if not validate_required(BN, "Batch Number")[0]:
                errors.append(validate_required(BN, "Batch Number")[1])
            if not validate_required(SN, "Serial Number")[0]:
                errors.append(validate_required(SN, "Serial Number")[1])
            
            # Check serial number uniqueness
            if SN and check_serial_exists(SN, [
                "/Users/apple/Desktop/2nd year/Python Project sem 3/officestock.csv",
                "/Users/apple/Desktop/2nd year/Python Project sem 3/hospitalstock.csv"
            ]):
                errors.append("Serial Number already exists. Please use a unique serial number.")
            
            # Validate dates
            date_valid, date_error = validate_dates(ENT, EXT)
            if not date_valid:
                errors.append(date_error)
            
            # Show errors if any
            if errors:
                error_msg = "Please fix the following errors:\n\n" + "\n".join(f"• {err}" for err in errors)
                tkinter.messagebox.showerror("Validation Error", error_msg)
                return
            
            # All validations passed, save data
            Lcsv=[ST,SZ,BN,SN,ENT,EXT]
            try:
                f=open("/Users/apple/Desktop/2nd year/Python Project sem 3/officestock.csv","a",newline="\n")
                cs=csv.writer(f)
                cs.writerow(Lcsv)
                f.close()
                tkinter.messagebox.showinfo("Entry Page", "Entry Registered Successfully")
                # Clear form
                sc1.set("")
                e11.delete(0, END)
                e21.delete(0, END)
                e31.delete(0, END)
            except Exception as e:
                tkinter.messagebox.showerror("Error", f"Failed to save entry: {str(e)}")
        s=customtkinter.CTkLabel(root1,text="Stent Type",font=("PT Sans Narrow",20),anchor=W).grid(row=1,column=0,padx=10,pady=10)
        sc1=customtkinter.CTkComboBox(root1,values=So,width=250,fg_color='#F8F1FF')
        sc1.grid(row=1,column=1,sticky=W)
        sc1.bind('<Return>', go_to_next_element)

        sz=customtkinter.CTkLabel(root1,text="Stent Size",font=("PT Sans Narrow",20),anchor=W).grid(row=2,column=0,padx=10,pady=10)
        e11=customtkinter.CTkEntry(root1,width=250,fg_color='#F8F1FF')
        e11.bind('<Return>', go_to_next_element)
        e11.grid(row=2,column=1,sticky=W)

        bn=customtkinter.CTkLabel(root1,text="Batch Number",font=("PT Sans Narrow",20),anchor=W).grid(row=3,column=0,padx=10,pady=10)
        e21=customtkinter.CTkEntry(root1,width=250,fg_color='#F8F1FF')
        e21.bind('<Return>', go_to_next_element)
        e21.grid(row=3,column=1,sticky=W)

        sn=customtkinter.CTkLabel(root1,text="Serial Number",font=("PT Sans Narrow",20),anchor=W).grid(row=4,column=0,padx=10,pady=10)
        e31=customtkinter.CTkEntry(root1,width=250,fg_color='#F8F1FF')
        e31.bind('<Return>', go_to_next_element)
        e31.bind('<KeyRelease>', lambda e: validate_serial_realtime(e31, [
            "/Users/apple/Desktop/2nd year/Python Project sem 3/officestock.csv",
            "/Users/apple/Desktop/2nd year/Python Project sem 3/hospitalstock.csv"
        ]))
        e31.grid(row=4,column=1,sticky=W)

        ce=customtkinter.CTkLabel(root1,text="Entry Date(DD/MM/YYYY)",font=("PT Sans Narrow",20),anchor=W).grid(row=5,column=0,padx=10,pady=10)
        cale= Calendar(root1,select="day",font=("",13))
        cale.grid(row=5,column=1,pady=10)

        cx=customtkinter.CTkLabel(root1,text="Expiry Date(DD/MM/YYYY)",font=("PT Sans Narrow",20),anchor=W).grid(row=1,column=3,padx=10,pady=10,rowspan=3)
        calx= Calendar(root1,select="day",font=("",13))
        calx.grid(row=1,column=4,pady=10,rowspan=3)

        b1=customtkinter.CTkButton(root1,text="Enter Data",font=("bold",15),height=40,corner_radius=20,width=200,fg_color='#1CAC78',hover_color='#00563B',command=ent1).grid(row=7,column=0,pady=10)
        b2=customtkinter.CTkButton(root1,text="Home",font=("bold",15),height=40,corner_radius=20,width=200,command=homee,fg_color='#AB0003',hover_color='#660000').grid(row=7,column=4)
        
        #HOSPITAL TAB
        def ent2():
            H=hc2.get()
            ST=sc2.get()
            SZ=e12.get().strip()
            BN=e22.get().strip()
            SN=e32.get().strip()
            ENT=str(cale.get_date())
            EXT=str(calx.get_date())
            
            # Validation
            errors = []
            
            # Validate required fields
            if not H or H.strip() == "":
                errors.append("Hospital Name is required")
            if not ST or ST.strip() == "":
                errors.append("Stent Type is required")
            if not validate_required(SZ, "Stent Size")[0]:
                errors.append(validate_required(SZ, "Stent Size")[1])
            if not validate_required(BN, "Batch Number")[0]:
                errors.append(validate_required(BN, "Batch Number")[1])
            if not validate_required(SN, "Serial Number")[0]:
                errors.append(validate_required(SN, "Serial Number")[1])
            
            # Check serial number uniqueness
            if SN and check_serial_exists(SN, [
                "/Users/apple/Desktop/2nd year/Python Project sem 3/officestock.csv",
                "/Users/apple/Desktop/2nd year/Python Project sem 3/hospitalstock.csv"
            ]):
                errors.append("Serial Number already exists. Please use a unique serial number.")
            
            # Validate dates
            date_valid, date_error = validate_dates(ENT, EXT)
            if not date_valid:
                errors.append(date_error)
            
            # Show errors if any
            if errors:
                error_msg = "Please fix the following errors:\n\n" + "\n".join(f"• {err}" for err in errors)
                tkinter.messagebox.showerror("Validation Error", error_msg)
                return
            
            # All validations passed, save data
            Lcsv=[H,ST,SZ,BN,SN,ENT,EXT]
            try:
                f=open("/Users/apple/Desktop/2nd year/Python Project sem 3/hospitalstock.csv","a",newline="\n")
                cs=csv.writer(f)
                cs.writerow(Lcsv)
                f.close()
                tkinter.messagebox.showinfo("Entry Page", "Entry Registered Successfully")
                # Clear form
                hc2.set("")
                sc2.set("")
                e12.delete(0, END)
                e22.delete(0, END)
                e32.delete(0, END)
            except Exception as e:
                tkinter.messagebox.showerror("Error", f"Failed to save entry: {str(e)}")
        h=customtkinter.CTkLabel(root2,text="Hospital Name",font=("PT Sans Narrow",20),anchor=W).grid(row=1,column=0,padx=10,pady=10)
        hc2=customtkinter.CTkComboBox(root2,values=Ho,width=250,fg_color='#F8F1FF')
        hc2.grid(row=1,column=1,sticky=W)
        hc2.bind('<Return>', go_to_next_element)

        s=customtkinter.CTkLabel(root2,text="Stent Type",font=("PT Sans Narrow",20),anchor=W).grid(row=2,column=0,padx=10,pady=10)
        sc2=customtkinter.CTkComboBox(root2,values=So,width=250,fg_color='#F8F1FF')
        sc2.grid(row=2,column=1,sticky=W)
        sc2.bind('<Return>', go_to_next_element)

        sz=customtkinter.CTkLabel(root2,text="Stent Size",font=("PT Sans Narrow",20),anchor=W).grid(row=3,column=0,padx=10,pady=10)
        e12=customtkinter.CTkEntry(root2,width=250,fg_color='#F8F1FF')
        e12.bind('<Return>', go_to_next_element)
        e12.grid(row=3,column=1,sticky=W)

        bn=customtkinter.CTkLabel(root2,text="Batch Number",font=("PT Sans Narrow",20),anchor=W).grid(row=4,column=0,padx=10,pady=10)
        e22=customtkinter.CTkEntry(root2,width=250,fg_color='#F8F1FF')
        e22.bind('<Return>', go_to_next_element)
        e22.grid(row=4,column=1,sticky=W)

        sn=customtkinter.CTkLabel(root2,text="Serial Number",font=("PT Sans Narrow",20),anchor=W).grid(row=5,column=0,padx=10,pady=10)
        e32=customtkinter.CTkEntry(root2,width=250,fg_color='#F8F1FF')
        e32.bind('<Return>', go_to_next_element)
        e32.bind('<KeyRelease>', lambda e: validate_serial_realtime(e32, [
            "/Users/apple/Desktop/2nd year/Python Project sem 3/officestock.csv",
            "/Users/apple/Desktop/2nd year/Python Project sem 3/hospitalstock.csv"
        ]))
        e32.grid(row=5,column=1,sticky=W)

        ce=customtkinter.CTkLabel(root2,text="Entry Date(DD/MM/YYYY)",font=("PT Sans Narrow",20),anchor=W).grid(row=1,column=3,padx=10,pady=10,rowspan=3)
        cale= Calendar(root2,select="day",font=("",13))
        cale.grid(row=1,column=4,pady=10,rowspan=3)

        cx=customtkinter.CTkLabel(root2,text="Expiry Date(DD/MM/YYYY)",font=("PT Sans Narrow",20),anchor=W).grid(row=4,column=3,padx=10,pady=10,rowspan=3)
        calx= Calendar(root2,select="day",font=("",13))
        calx.grid(row=4,column=4,pady=10,rowspan=3)

        b1=customtkinter.CTkButton(root2,text="Enter Data",font=("bold",15),height=40,corner_radius=20,width=200,fg_color='#1CAC78',hover_color='#00563B',command=ent2).grid(row=8,column=0,pady=10)
        b2=customtkinter.CTkButton(root2,text="Home",font=("bold",15),height=40,corner_radius=20,width=200,command=homee,fg_color='#AB0003',hover_color='#660000').grid(row=8,column=4)

        #USED STENT TAB
        def ent3():
            D=dc3.get()
            H=hc3.get()
            PN=e53.get().strip()
            BA=e63.get().strip()
            IPD=e73.get().strip()
            CN=e83.get().strip()
            BNo=e93.get().strip()
            ST=sc3.get()
            SZ=e13.get().strip()
            BN=e23.get().strip()
            SN=e33.get().strip()
            ENT=str(cale.get_date())
            EXT=str(calx.get_date())
            
            # Validation
            errors = []
            
            # Validate required fields
            if not D or D.strip() == "":
                errors.append("Doctor Name is required")
            if not H or H.strip() == "":
                errors.append("Hospital Name is required")
            if not validate_required(PN, "Patient Name")[0]:
                errors.append(validate_required(PN, "Patient Name")[1])
            if not validate_required(BA, "Bill Amount")[0]:
                errors.append(validate_required(BA, "Bill Amount")[1])
            if not validate_required(IPD, "I.P.D.")[0]:
                errors.append(validate_required(IPD, "I.P.D.")[1])
            if not validate_required(CN, "Cath Number")[0]:
                errors.append(validate_required(CN, "Cath Number")[1])
            if not validate_required(BNo, "Bill Number")[0]:
                errors.append(validate_required(BNo, "Bill Number")[1])
            if not ST or ST.strip() == "":
                errors.append("Stent Type is required")
            if not validate_required(SZ, "Stent Size")[0]:
                errors.append(validate_required(SZ, "Stent Size")[1])
            if not validate_required(BN, "Batch Number")[0]:
                errors.append(validate_required(BN, "Batch Number")[1])
            if not validate_required(SN, "Serial Number")[0]:
                errors.append(validate_required(SN, "Serial Number")[1])
            
            # Validate numeric fields
            if BA:
                num_valid, num_error = validate_numeric(BA, "Bill Amount")
                if not num_valid:
                    errors.append(num_error)
                elif float(BA) < 0:
                    errors.append("Bill Amount cannot be negative")
            
            # Validate serial number for used stents - must exist in stock and not already be used
            if SN:
                serial_in_stock, serial_already_used = check_serial_available_for_use(SN)
                if serial_already_used:
                    errors.append("Serial Number is already marked as used. Cannot use the same serial number twice.")
                elif not serial_in_stock:
                    errors.append("Serial Number not found in office stock or hospital stock. Please enter a valid serial number that exists in inventory.")
            
            # Validate dates
            date_valid, date_error = validate_dates(ENT, EXT)
            if not date_valid:
                errors.append(date_error)
            
            # Show errors if any
            if errors:
                error_msg = "Please fix the following errors:\n\n" + "\n".join(f"• {err}" for err in errors)
                tkinter.messagebox.showerror("Validation Error", error_msg)
                return
            
            # All validations passed, save data
            Lcsv=[D,H,PN,BA,IPD,CN,BNo,ST,SZ,BN,SN,ENT,EXT]
            Hospital=[H,ST,SZ,BN,SN,ENT,EXT]
            
            try:
                # Save to dedicated stentused.csv file
                f=open("/Users/apple/Desktop/2nd year/Python Project sem 3/stentused.csv","a",newline="\n")
                cs=csv.writer(f)
                cs.writerow(Lcsv)
                f.close()
                tkinter.messagebox.showinfo("Entry Page", "Entry Registered Successfully")
                # Clear form
                dc3.set("")
                hc3.set("")
                e53.delete(0, END)
                e63.delete(0, END)
                e73.delete(0, END)
                e83.delete(0, END)
                e93.delete(0, END)
                sc3.set("")
                e13.delete(0, END)
                e23.delete(0, END)
                e33.delete(0, END)
            except Exception as e:
                tkinter.messagebox.showerror("Error", f"Failed to save entry: {str(e)}")
        d=customtkinter.CTkLabel(root3,text="Doctor Name",font=("PT Sans Narrow",20),anchor=W).grid(row=1,column=0,padx=10,pady=10)
        dc3=customtkinter.CTkComboBox(root3,values=Do,width=250,fg_color='#F8F1FF')
        dc3.grid(row=1,column=1,sticky=W)
        dc3.bind('<Return>', go_to_next_element)

        h=customtkinter.CTkLabel(root3,text="Hospital Name",font=("PT Sans Narrow",20),anchor=W).grid(row=2,column=0,padx=10,pady=10)
        hc3=customtkinter.CTkComboBox(root3,values=Ho,width=250,fg_color='#F8F1FF')
        hc3.grid(row=2,column=1,sticky=W)
        hc3.bind('<Return>', go_to_next_element)

        pn=customtkinter.CTkLabel(root3,text="Patient Name",font=("PT Sans Narrow",20),anchor=W).grid(row=3,column=0,padx=10,pady=10)
        e53=customtkinter.CTkEntry(root3,width=250,fg_color='#F8F1FF')
        e53.bind('<Return>', go_to_next_element)
        e53.grid(row=3,column=1,sticky=W)

        bm=customtkinter.CTkLabel(root3,text="Bill Ammount",font=("PT Sans Narrow",20),anchor=W).grid(row=4,column=0,padx=10,pady=10)
        e63=customtkinter.CTkEntry(root3,width=250,fg_color='#F8F1FF')
        e63.bind('<Return>', go_to_next_element)
        e63.bind('<KeyRelease>', lambda e: validate_numeric_realtime(e63, "Bill Amount"))
        e63.grid(row=4,column=1,sticky=W)

        ip=customtkinter.CTkLabel(root3,text="I.P.D.",font=("PT Sans Narrow",20),anchor=W).grid(row=5,column=0,padx=10,pady=10)
        e73=customtkinter.CTkEntry(root3,width=250,fg_color='#F8F1FF')
        e73.bind('<Return>', go_to_next_element)
        e73.grid(row=5,column=1,sticky=W)

        cn=customtkinter.CTkLabel(root3,text="Cath Number",font=("PT Sans Narrow",20),anchor=W).grid(row=6,column=0,padx=10,pady=10)
        e83=customtkinter.CTkEntry(root3,width=250,fg_color='#F8F1FF')
        e83.bind('<Return>', go_to_next_element)
        e83.grid(row=6,column=1,sticky=W)

        bnn=customtkinter.CTkLabel(root3,text="Bill Number",font=("PT Sans Narrow",20),anchor=W).grid(row=7,column=0,padx=10,pady=10)
        e93=customtkinter.CTkEntry(root3,width=250,fg_color='#F8F1FF')
        e93.bind('<Return>', go_to_next_element)
        e93.grid(row=7,column=1,sticky=W)

        s=customtkinter.CTkLabel(root3,text="Stent Type",font=("PT Sans Narrow",20),anchor=W).grid(row=8,column=0,padx=10,pady=10)
        sc3=customtkinter.CTkComboBox(root3,values=So,width=250,fg_color='#F8F1FF')
        sc3.grid(row=8,column=1,sticky=W)
        sc3.bind('<Return>', go_to_next_element)

        sz=customtkinter.CTkLabel(root3,text="Stent Size",font=("PT Sans Narrow",20),anchor=W).grid(row=9,column=0,padx=10,pady=10)
        e13=customtkinter.CTkEntry(root3,width=250,fg_color='#F8F1FF')
        e13.bind('<Return>', go_to_next_element)
        e13.grid(row=9,column=1,sticky=W)

        bn=customtkinter.CTkLabel(root3,text="Batch Number",font=("PT Sans Narrow",20),anchor=W).grid(row=1,column=3,padx=10,pady=10)
        e23=customtkinter.CTkEntry(root3,width=250,fg_color='#F8F1FF')
        e23.bind('<Return>', go_to_next_element)
        e23.grid(row=1,column=4,sticky=W)

        sn=customtkinter.CTkLabel(root3,text="Serial Number",font=("PT Sans Narrow",20),anchor=W).grid(row=2,column=3,padx=10,pady=10)
        e33=customtkinter.CTkEntry(root3,width=250,fg_color='#F8F1FF')
        e33.bind('<Return>', go_to_next_element)
        def validate_used_serial_realtime(event):
            """Real-time validation for serial number in used stent entry"""
            serial = e33.get().strip()
            if serial:
                serial_in_stock, serial_already_used = check_serial_available_for_use(serial)
                if serial_already_used:
                    highlight_field(e33, False)
                    return False
                elif not serial_in_stock:
                    highlight_field(e33, False)
                    return False
                else:
                    highlight_field(e33, True)
                    return True
            return None
        
        e33.bind('<KeyRelease>', validate_used_serial_realtime)
        e33.grid(row=2,column=4,sticky=W)

        ce=customtkinter.CTkLabel(root3,text="Entry Date(DD/MM/YYYY)",font=("PT Sans Narrow",20),anchor=W).grid(row=3,column=3,padx=10,pady=10,rowspan=3)
        cale= Calendar(root3,select="day",font=("",13))
        cale.grid(row=3,column=4,pady=10,rowspan=3)

        c=customtkinter.CTkLabel(root3,text="Expiry Date(DD/MM/YYYY)",font=("PT Sans Narrow",20),anchor=W).grid(row=6,column=3,padx=10,pady=10,rowspan=3)
        cal= Calendar(root3,select="day",font=("",13))
        cal.grid(row=6,column=4,pady=10,rowspan=3)

        b1=customtkinter.CTkButton(root3,text="Enter Data",font=("bold",15),height=40,corner_radius=20,width=200,fg_color='#1CAC78',hover_color='#00563B',command=ent3).grid(row=9,column=3,pady=10)
        b2=customtkinter.CTkButton(root3,text="Home",font=("bold",15),height=40,corner_radius=20,width=200,command=homee,fg_color='#AB0003',hover_color='#660000').grid(row=9,column=4)
    def SU(): #STENTS USED
        nonlocal current_view, is_loading
        if is_loading:
            return
        is_loading = True
        
        def homee():#HOME BUTTON
            nonlocal current_view, is_loading
            if current_view:
                try:
                    current_view.destroy()
                except:
                    pass
            is_loading = False
            show_dashboard()
        def ent2():#HOSPITAL TO USED
            def ent23():
                f=open("/Users/apple/Desktop/2nd year/Python Project sem 3/hospitalstock.csv","r")
                f1=open("b.csv","w")
                cd=csv.writer(f1)
                cs=csv.reader(f)
                Lcsv=[]
                serialno=0
                for i in cs:
                    if i:
                        if len(i)>4:
                            if i[3]!=serialno:
                                cd.writerow(i)

                            else:
                                Lcsv.append(i)
                f.close()
                f1.close()
                os.remove("/Users/apple/Desktop/2nd year/Python Project sem 3/hospitalstock.csv")
                os.rename("b.csv","/Users/apple/Desktop/2nd year/Python Project sem 3/hospitalstock.csv")
                
                D=hc2.get()
                PN=e53.get()
                BA=e63.get()
                IPD=e73.get()
                CN=e83.get()
                BNo=e93.get()
                
                stent=[D,A[0],PN,BA,IPD,CN,BNo,A[1],A[2],A[3],A[4],A[5],A[6]]
                g=open("/Users/apple/Desktop/2nd year/Python Project sem 3/officestock.csv","a",newline="\n")
                cf=csv.writer(g)
                cf.writerow(stent)
                g.close()
                tkinter.messagebox.showinfo("Stent transfer", "Transfered Successfully")
            f=open("/Users/apple/Desktop/2nd year/Python Project sem 3/Dets.csv","r")
            r=csv.reader(f)
            Do=[]
            for i in r:
                if i and len(i) > 1 and i[1]!="":
                    Do.append(i[1].strip())
            f.close()
            # Remove duplicates while preserving order
            Do = list(dict.fromkeys(Do))
            b=e312.get()

            f=open("/Users/apple/Desktop/2nd year/Python Project sem 3/hospitalstock.csv")
            r=csv.reader(f)
            c=0
            for i in r:
                if i:
                    if i[4]==b:
                        A=i
                        print(A)
            f.close()            
            tree=ttk.Treeview(root2,columns=("H","ST","SZ","BN","SN","ENT","EXT"),show='headings',height=1)


            tree.column("#1")
            tree.column("#2")
            tree.column("#3")
            tree.column("#4")
            tree.column("#5")
            tree.column("#6")
            tree.column("#7")

            tree.heading("H",text="Hospital Name")
            tree.heading("ST",text="Stent Type")
            tree.heading("SZ",text="Stent Size")
            tree.heading("BN",text="Batch Number")
            tree.heading("SN",text="Serial Number")
            tree.heading("ENT",text="Entry Date")
            tree.heading("EXT",text="Expiry Date")

            tree.insert('',END,values=tuple(A))
            tree.grid(row=2,column=0,columnspan=3)

            h=customtkinter.CTkLabel(root2,text="Doctor Name",font=("PT Sans Narrow",20),anchor=W).grid(row=3,column=0,padx=10,pady=10)
            hc2=customtkinter.CTkComboBox(root2,values=Do,width=250,fg_color='#F8F1FF')
            hc2.grid(row=3,column=1,sticky=W)

            pn=customtkinter.CTkLabel(root2,text="Patient Name",font=("PT Sans Narrow",20),anchor=W).grid(row=4,column=0,padx=10,pady=10)
            e53=customtkinter.CTkEntry(root2,width=250,fg_color='#F8F1FF')
            e53.bind('<Return>', go_to_next_element)
            e53.grid(row=4,column=1,sticky=W)

            bm=customtkinter.CTkLabel(root2,text="Bill Ammount",font=("PT Sans Narrow",20),anchor=W).grid(row=5,column=0,padx=10,pady=10)
            e63=customtkinter.CTkEntry(root2,width=250,fg_color='#F8F1FF')
            e63.bind('<Return>', go_to_next_element)
            e63.grid(row=5,column=1,sticky=W)

            ip=customtkinter.CTkLabel(root2,text="I.P.D.",font=("PT Sans Narrow",20),anchor=W).grid(row=6,column=0,padx=10,pady=10)
            e73=customtkinter.CTkEntry(root2,width=250,fg_color='#F8F1FF')
            e73.bind('<Return>', go_to_next_element)
            e73.grid(row=6,column=1,sticky=W)

            cn=customtkinter.CTkLabel(root2,text="Cath Number",font=("PT Sans Narrow",20),anchor=W).grid(row=7,column=0,padx=10,pady=10)
            e83=customtkinter.CTkEntry(root2,width=250,fg_color='#F8F1FF')
            e83.bind('<Return>', go_to_next_element)
            e83.grid(row=7,column=1,sticky=W)

            bnn=customtkinter.CTkLabel(root2,text="Bill Number",font=("PT Sans Narrow",20),anchor=W).grid(row=8,column=0,padx=10,pady=10)
            e93=customtkinter.CTkEntry(root2,width=250,fg_color='#F8F1FF')
            e93.bind('<Return>', go_to_next_element)
            e93.grid(row=8,column=1,sticky=W)


            bn=customtkinter.CTkButton(root2,text="Transfer",font=("bold",15),height=40,corner_radius=20,width=200,fg_color='#1CAC78',hover_color='#00563B',command=ent23).grid(row=9,column=0,pady=10,padx=20)
           

        def ent():#OFFICE TO HOSPITAL
            def ent2():
                f=open("/Users/apple/Desktop/2nd year/Python Project sem 3/officestock.csv","r")
                f1=open("a.csv","w")
                cd=csv.writer(f1)
                cs=csv.reader(f)
                Lcsv=[]
                serialno=e31.get()
                for i in cs:
                    if i:
                        if len(i)>4:
                            if i[3]!=serialno:
                                cd.writerow(i)

                            else:
                                Lcsv.append(i)
                f.close()
                f1.close()
                os.remove("/Users/apple/Desktop/2nd year/Python Project sem 3/officestock.csv")
                os.rename("a.csv","/Users/apple/Desktop/2nd year/Python Project sem 3/officestock.csv")

                h=hc2.get()
                A.insert(0,h)
                g=open("/Users/apple/Desktop/2nd year/Python Project sem 3/hospitalstock.csv","a",newline="\n")
                cf=csv.writer(g)
                cf.writerow(A)
                tkinter.messagebox.showinfo("Stent transfer", "Transfered Successfully")

                g.close()
            f=open("/Users/apple/Desktop/2nd year/Python Project sem 3/Dets.csv","r")
            r=csv.reader(f)
            #f.close()
            Ho=[]
            for i in r:
                if i and len(i) > 0 and i[0]!="":
                    Ho.append(i[0].strip())
            f.close()
            # Remove duplicates while preserving order
            Ho = list(dict.fromkeys(Ho))
            b=e31.get()
            
            f=open("/Users/apple/Desktop/2nd year/Python Project sem 3/officestock.csv")
            r=csv.reader(f)
            c=0
            for i in r:
                if i:
                    if i[3]==b:
                        A=i
            f.close()            
            tree=ttk.Treeview(root1,columns=("ST","SZ","BN","SN","ENT","EXT"),show='headings',height=1)

            tree.column("#1")
            tree.column("#2")
            tree.column("#3")
            tree.column("#4")
            tree.column("#5")
            tree.column("#6")

            tree.heading("ST",text="Stent Type")
            tree.heading("SZ",text="Stent Size")
            tree.heading("BN",text="Batch Number")
            tree.heading("SN",text="Serial Number")
            tree.heading("ENT",text="Entry Date")
            tree.heading("EXT",text="Expiry Date")

            tree.insert('',END,values=tuple(A))
            tree.grid(row=2,column=0,columnspan=2)

            h=customtkinter.CTkLabel(root1,text="Hospital Name",font=("PT Sans Narrow",20),anchor=W).grid(row=3,column=0,padx=10,pady=10)
            hc2=customtkinter.CTkComboBox(root1,values=Ho,width=250,fg_color='#F8F1FF')
            hc2.grid(row=3,column=1,sticky=W)

            bn=customtkinter.CTkButton(root1,text="Transfer",font=("bold",15),height=40,corner_radius=20,width=200,fg_color='#1CAC78',hover_color='#00563B',command=ent2).grid(row=4,column=0,pady=10,padx=20)
            b2=customtkinter.CTkButton(root2,text="Home",font=("bold",15),height=40,corner_radius=20,width=200,command=homee,fg_color='#AB0003',hover_color='#660000').grid(row=4,column=1)


                        
        #TAB              
        if current_view:
            try:
                current_view.destroy()
            except:
                pass
        root = customtkinter.CTkTabview(master=content_frame,height=600,width=1100)
        root.pack(fill="both", expand=True, padx=10, pady=10)
        current_view = root
        is_loading = False

        root1=root.add("Office → Hospital")
        root2=root.add("Hospital → Used")
        b2=customtkinter.CTkButton(root1,text="Home",font=("bold",15),height=40,corner_radius=20,width=200,command=homee,fg_color='#AB0003',hover_color='#660000').grid(row=4,column=1)

        sn=customtkinter.CTkLabel(root1,text="Serial Number",font=("PT Sans Narrow",20),anchor=W).grid(row=0,column=0,padx=10,pady=10)
        e31=customtkinter.CTkEntry(root1,width=250,fg_color='#F8F1FF')
        e31.bind('<Return>', go_to_next_element)
        e31.grid(row=0,column=1,sticky=W)

        b1=customtkinter.CTkButton(root1,text="Search",font=("bold",15),height=40,corner_radius=20,width=200,fg_color='#1CAC78',hover_color='#00563B',command=ent).grid(row=0,column=2,pady=10,padx=20)

        sn2=customtkinter.CTkLabel(root2,text="Serial Number",font=("PT Sans Narrow",20),anchor=W).grid(row=0,column=0,padx=10,pady=10)
        e312=customtkinter.CTkEntry(root2,width=250,fg_color='#F8F1FF')
        e312.bind('<Return>', go_to_next_element)
        e312.grid(row=0,column=1,sticky=W)

        b12=customtkinter.CTkButton(root2,text="Search",font=("bold",15),height=40,corner_radius=20,width=200,fg_color='#1CAC78',hover_color='#00563B',command=ent2).grid(row=0,column=2,pady=10,padx=20)
        b2=customtkinter.CTkButton(root2,text="Home",font=("bold",15),height=40,corner_radius=20,width=200,command=homee,fg_color='#AB0003',hover_color='#660000').grid(row=9,column=1)
    def DU():#DATA UPDATION
        nonlocal current_view, is_loading
        if is_loading:
            return
        is_loading = True

        def homee():
            nonlocal current_view, is_loading
            if current_view:
                try:
                    current_view.destroy()
                except:
                    pass
            is_loading = False
            show_dashboard()

        def parse_date(date_str):
            """Parse date string to datetime object, handling multiple formats"""
            if not date_str:
                return None
            date_str = str(date_str).strip()
            # Try different date formats
            formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%m-%d-%Y"]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
            return None
        
        def search_and_update():
            nonlocal current_view
            serial_num = serial_entry.get().strip()
            if not serial_num:
                tkinter.messagebox.showerror("Error", "Please enter a serial number")
                return
            
            # Check if at least one field is selected
            if not (c1.get() or c2.get() or c3.get() or c4.get() or c5.get() or 
                    c6.get() or c7.get() or c8.get() or c9.get() or c10.get() or 
                    c11.get() or c12.get()):
                tkinter.messagebox.showwarning("Warning", "Please select at least one field to update")
                return
            
            # Search for the record in all CSV files
            record_found = False
            record_data = None
            file_type = None
            file_path = None
            
            # Search in stentused.csv first (used stents - 13 columns)
            try:
                f = open("/Users/apple/Desktop/2nd year/Python Project sem 3/stentused.csv", "r", errors="ignore")
                reader = csv.reader(f)
                for row in reader:
                    if row and len(row) >= 13:
                        # Used stent entry format: [Doctor, Hospital, Patient, Bill Amt, IPD, Cath, Bill No, Stent Type, Size, Batch, Serial, Entry, Expiry]
                        # Serial is at index 10
                        used_serial = str(row[10]).strip() if len(row) > 10 else ""
                        if used_serial == serial_num:
                            record_data = row
                            file_type = "used"
                            file_path = "/Users/apple/Desktop/2nd year/Python Project sem 3/stentused.csv"
                            record_found = True
                            break
                f.close()
            except Exception as e:
                print(f"Error reading stentused.csv: {e}")
            
            # Search in officestock.csv (office stock - 6 columns: Stent Type, Size, Batch, Serial, Entry, Expiry)
            if not record_found:
                try:
                    f = open("/Users/apple/Desktop/2nd year/Python Project sem 3/officestock.csv", "r", errors="ignore")
                    reader = csv.reader(f)
                    for row in reader:
                        if row and len(row) >= 6:
                            serial_col = str(row[3]).strip() if len(row) > 3 else ""
                            # Check for office stock (6 columns, serial at index 3)
                            if serial_col == serial_num:
                                record_data = row
                                file_type = "office"
                                file_path = "/Users/apple/Desktop/2nd year/Python Project sem 3/officestock.csv"
                                record_found = True
                                break
                    f.close()
                except Exception as e:
                    print(f"Error reading officestock.csv: {e}")
            
            # Search in hospitalstock.csv if not found (7 columns: Hospital, Stent Type, Size, Batch, Serial, Entry, Expiry)
            if not record_found:
                try:
                    f = open("/Users/apple/Desktop/2nd year/Python Project sem 3/hospitalstock.csv", "r", errors="ignore")
                    reader = csv.reader(f)
                    for row in reader:
                        if row and len(row) >= 5:
                            hospital_serial = str(row[4]).strip() if len(row) > 4 else ""
                            if hospital_serial == serial_num:
                                record_data = row
                                file_type = "hospital"
                                file_path = "/Users/apple/Desktop/2nd year/Python Project sem 3/hospitalstock.csv"
                                record_found = True
                                break
                    f.close()
                except Exception as e:
                    print(f"Error reading hospitalstock.csv: {e}")
            
            if not record_found:
                tkinter.messagebox.showerror("Error", f"Serial number {serial_num} not found in any file")
                return
            
            # Load dropdown values
            try:
                f = open("/Users/apple/Desktop/2nd year/Python Project sem 3/Dets.csv", "r", errors="ignore")
                r = csv.reader(f)
                Ho = []
                Do = []
                So = []
                for i in r:
                    if len(i) > 0 and i[0] != "":
                        Ho.append(i[0].strip())
                    if len(i) > 1 and i[1] != "":
                        Do.append(i[1].strip())
                    if len(i) > 2 and i[2] != "":
                        So.append(i[2].strip())
                f.close()
                # Remove duplicates while preserving order
                Ho = list(dict.fromkeys(Ho))
                Do = list(dict.fromkeys(Do))
                So = list(dict.fromkeys(So))
            except Exception as e:
                tkinter.messagebox.showerror("Error", f"Failed to load dropdown values: {str(e)}")
                return
            
            # Destroy current view and create update form
            if current_view:
                try:
                    current_view.destroy()
                except:
                    pass
            
            update_frame = customtkinter.CTkFrame(master=content_frame)
            update_frame.pack(fill="both", expand=True, padx=10, pady=10)
            current_view = update_frame
            
            # Create scrollable frame for form fields
            scroll_frame = customtkinter.CTkScrollableFrame(update_frame, fg_color="transparent")
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Store widgets and values
            widget_vars = {}
            row_num = 0
            
            def save_updates():
                updates = {}
                file_to_update = file_path
                validation_errors = []
                
                # Collect updated values based on checkboxes and file type
                if file_type == "office":
                    # Office stock: [Stent Type, Size, Batch, Serial, Entry, Expiry]
                    if c3.get() and "stent_type" in widget_vars:
                        value = widget_vars["stent_type"].get()
                        if not value or value.strip() == "":
                            validation_errors.append("Stent Type cannot be empty")
                        else:
                            updates[0] = value
                    if c4.get() and "stent_size" in widget_vars:
                        value = widget_vars["stent_size"].get().strip()
                        if not value:
                            validation_errors.append("Stent Size cannot be empty")
                        else:
                            updates[1] = value
                    if c5.get() and "batch" in widget_vars:
                        value = widget_vars["batch"].get().strip()
                        if not value:
                            validation_errors.append("Batch Number cannot be empty")
                        else:
                            updates[2] = value
                    if c6.get() and "entry_date" in widget_vars:
                        updates[4] = str(widget_vars["entry_date"].get_date())
                    if c7.get() and "expiry_date" in widget_vars:
                        updates[5] = str(widget_vars["expiry_date"].get_date())
                        
                    # Validate dates
                    if 4 in updates and 5 in updates:
                        entry_date = parse_date(updates[4])
                        expiry_date = parse_date(updates[5])
                        if entry_date and expiry_date and expiry_date <= entry_date:
                            validation_errors.append("Expiry date must be after entry date")
                            
                elif file_type == "hospital":
                    # Hospital stock: [Hospital, Stent Type, Size, Batch, Serial, Entry, Expiry]
                    if c1.get() and "hospital" in widget_vars:
                        value = widget_vars["hospital"].get()
                        if not value or value.strip() == "":
                            validation_errors.append("Hospital Name cannot be empty")
                        else:
                            updates[0] = value
                    if c3.get() and "stent_type" in widget_vars:
                        value = widget_vars["stent_type"].get()
                        if not value or value.strip() == "":
                            validation_errors.append("Stent Type cannot be empty")
                        else:
                            updates[1] = value
                    if c4.get() and "stent_size" in widget_vars:
                        value = widget_vars["stent_size"].get().strip()
                        if not value:
                            validation_errors.append("Stent Size cannot be empty")
                        else:
                            updates[2] = value
                    if c5.get() and "batch" in widget_vars:
                        value = widget_vars["batch"].get().strip()
                        if not value:
                            validation_errors.append("Batch Number cannot be empty")
                        else:
                            updates[3] = value
                    if c6.get() and "entry_date" in widget_vars:
                        updates[5] = str(widget_vars["entry_date"].get_date())
                    if c7.get() and "expiry_date" in widget_vars:
                        updates[6] = str(widget_vars["expiry_date"].get_date())
                        
                    # Validate dates
                    if 5 in updates and 6 in updates:
                        entry_date = parse_date(updates[5])
                        expiry_date = parse_date(updates[6])
                        if entry_date and expiry_date and expiry_date <= entry_date:
                            validation_errors.append("Expiry date must be after entry date")
                            
                elif file_type == "used":
                    # Used stent: [Doctor, Hospital, Patient, Bill Amt, IPD, Cath, Bill No, Stent Type, Size, Batch, Serial, Entry, Expiry]
                    if c2.get() and "doctor" in widget_vars:
                        value = widget_vars["doctor"].get()
                        if not value or value.strip() == "":
                            validation_errors.append("Doctor Name cannot be empty")
                        else:
                            updates[0] = value
                    if c1.get() and "hospital" in widget_vars:
                        value = widget_vars["hospital"].get()
                        if not value or value.strip() == "":
                            validation_errors.append("Hospital Name cannot be empty")
                        else:
                            updates[1] = value
                    if c8.get() and "patient" in widget_vars:
                        value = widget_vars["patient"].get().strip()
                        if not value:
                            validation_errors.append("Patient Name cannot be empty")
                        else:
                            updates[2] = value
                    if c9.get() and "bill_amount" in widget_vars:
                        value = widget_vars["bill_amount"].get().strip()
                        if not value:
                            validation_errors.append("Bill Amount cannot be empty")
                        else:
                            try:
                                float(value)
                                if float(value) < 0:
                                    validation_errors.append("Bill Amount cannot be negative")
                                else:
                                    updates[3] = value
                            except:
                                validation_errors.append("Bill Amount must be a valid number")
                    if c10.get() and "ipd" in widget_vars:
                        value = widget_vars["ipd"].get().strip()
                        if not value:
                            validation_errors.append("I.P.D. cannot be empty")
                        else:
                            updates[4] = value
                    if c11.get() and "cath" in widget_vars:
                        value = widget_vars["cath"].get().strip()
                        if not value:
                            validation_errors.append("Cath Number cannot be empty")
                        else:
                            updates[5] = value
                    if c12.get() and "bill_no" in widget_vars:
                        value = widget_vars["bill_no"].get().strip()
                        if not value:
                            validation_errors.append("Bill Number cannot be empty")
                        else:
                            updates[6] = value
                    if c3.get() and "stent_type" in widget_vars:
                        value = widget_vars["stent_type"].get()
                        if not value or value.strip() == "":
                            validation_errors.append("Stent Type cannot be empty")
                        else:
                            updates[7] = value
                    if c4.get() and "stent_size" in widget_vars:
                        value = widget_vars["stent_size"].get().strip()
                        if not value:
                            validation_errors.append("Stent Size cannot be empty")
                        else:
                            updates[8] = value
                    if c5.get() and "batch" in widget_vars:
                        value = widget_vars["batch"].get().strip()
                        if not value:
                            validation_errors.append("Batch Number cannot be empty")
                        else:
                            updates[9] = value
                    if c6.get() and "entry_date" in widget_vars:
                        updates[11] = str(widget_vars["entry_date"].get_date())
                    if c7.get() and "expiry_date" in widget_vars:
                        updates[12] = str(widget_vars["expiry_date"].get_date())
                        
                    # Validate dates
                    if 11 in updates and 12 in updates:
                        entry_date = parse_date(updates[11])
                        expiry_date = parse_date(updates[12])
                        if entry_date and expiry_date and expiry_date <= entry_date:
                            validation_errors.append("Expiry date must be after entry date")
                
                # Show validation errors if any
                if validation_errors:
                    error_msg = "Please fix the following errors:\n\n" + "\n".join(f"• {err}" for err in validation_errors)
                    tkinter.messagebox.showerror("Validation Error", error_msg)
                    return
                
                if not updates:
                    tkinter.messagebox.showwarning("Warning", "No fields selected for update")
                    return
                
                # Update the record in the file
                try:
                    # Read all rows
                    f = open(file_to_update, "r", errors="ignore")
                    reader = csv.reader(f)
                    all_rows = list(reader)
                    f.close()
                    
                    # Find and update the row
                    row_updated = False
                    updated_rows = []
                    for i, row in enumerate(all_rows):
                        if row and len(row) > 0 and any(cell.strip() for cell in row if cell):
                            serial_index = 3 if file_type == "office" else (4 if file_type == "hospital" else 10)
                            if len(row) > serial_index and str(row[serial_index]).strip() == serial_num:
                                # Update the row - extend row if necessary
                                max_col = max(updates.keys()) if updates else 0
                                while len(row) <= max_col:
                                    row.append("")
                                # Update the row
                                for col_index, new_value in updates.items():
                                    if col_index < len(row):
                                        row[col_index] = str(new_value).strip()
                                updated_rows.append(row)
                                row_updated = True
                            else:
                                updated_rows.append(row)
                        elif row and len(row) > 0:
                            # Keep non-empty rows even if they don't match
                            updated_rows.append(row)
                    
                    if not row_updated:
                        tkinter.messagebox.showerror("Error", "Record not found in file. It may have been deleted.")
                        return
                    
                    # Write back to file
                    try:
                        f = open(file_to_update, "w", newline="", errors="ignore")
                        writer = csv.writer(f)
                        writer.writerows(updated_rows)
                        f.close()
                    except Exception as write_error:
                        tkinter.messagebox.showerror("Error", f"Failed to write to file: {str(write_error)}")
                        return
                    
                    tkinter.messagebox.showinfo("Success", "Record updated successfully!")
                    homee()
                except Exception as e:
                    tkinter.messagebox.showerror("Error", f"Failed to update record: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
            
            # Display current record and create update fields
            info_label = customtkinter.CTkLabel(scroll_frame, text=f"Updating Record - Serial: {serial_num} ({file_type.title()})", 
                                                font=("Helvetica Neue", 18, "bold"), text_color="#2f3b52")
            info_label.grid(row=0, column=0, columnspan=2, pady=10, padx=10)
            
            # Check if any fields will be displayed
            fields_to_show = sum([
                c1.get() and file_type in ["hospital", "used"],
                c2.get() and file_type == "used",
                c3.get(),
                c4.get(),
                c5.get(),
                c6.get(),
                c7.get(),
                c8.get() and file_type == "used",
                c9.get() and file_type == "used",
                c10.get() and file_type == "used",
                c11.get() and file_type == "used",
                c12.get() and file_type == "used"
            ])
            
            if fields_to_show == 0:
                no_fields_label = customtkinter.CTkLabel(scroll_frame, 
                    text="No fields selected that are applicable for this record type.", 
                    font=("PT Sans Narrow", 14), text_color="#ef4444")
                no_fields_label.grid(row=1, column=0, columnspan=2, pady=20, padx=10)
            
            # Create form fields based on file type and checkboxes
            if file_type == "used":
                # Used stent fields
                if c2.get():  # Doctor Name
                    customtkinter.CTkLabel(scroll_frame, text="Doctor Name", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    dc = customtkinter.CTkComboBox(scroll_frame, values=Do, width=250, fg_color='#F8F1FF')
                    dc.set(record_data[0] if len(record_data) > 0 else "")
                    dc.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["doctor"] = dc
                    row_num += 1
                
                if c1.get():  # Hospital Name
                    customtkinter.CTkLabel(scroll_frame, text="Hospital Name", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    hc = customtkinter.CTkComboBox(scroll_frame, values=Ho, width=250, fg_color='#F8F1FF')
                    hc.set(record_data[1] if len(record_data) > 1 else "")
                    hc.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["hospital"] = hc
                    row_num += 1
                
                if c8.get():  # Patient Name
                    customtkinter.CTkLabel(scroll_frame, text="Patient Name", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    pn_entry = customtkinter.CTkEntry(scroll_frame, width=250, fg_color='#F8F1FF')
                    pn_entry.insert(0, record_data[2] if len(record_data) > 2 else "")
                    pn_entry.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["patient"] = pn_entry
                    row_num += 1
                
                if c9.get():  # Bill Amount
                    customtkinter.CTkLabel(scroll_frame, text="Bill Amount", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    bm_entry = customtkinter.CTkEntry(scroll_frame, width=250, fg_color='#F8F1FF')
                    bm_entry.insert(0, record_data[3] if len(record_data) > 3 else "")
                    bm_entry.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["bill_amount"] = bm_entry
                    row_num += 1
                
                if c10.get():  # I.P.D.
                    customtkinter.CTkLabel(scroll_frame, text="I.P.D.", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    ipd_entry = customtkinter.CTkEntry(scroll_frame, width=250, fg_color='#F8F1FF')
                    ipd_entry.insert(0, record_data[4] if len(record_data) > 4 else "")
                    ipd_entry.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["ipd"] = ipd_entry
                    row_num += 1
                
                if c11.get():  # Cath Number
                    customtkinter.CTkLabel(scroll_frame, text="Cath Number", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    cn_entry = customtkinter.CTkEntry(scroll_frame, width=250, fg_color='#F8F1FF')
                    cn_entry.insert(0, record_data[5] if len(record_data) > 5 else "")
                    cn_entry.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["cath"] = cn_entry
                    row_num += 1
                
                if c12.get():  # Bill Number
                    customtkinter.CTkLabel(scroll_frame, text="Bill Number", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    bn_entry = customtkinter.CTkEntry(scroll_frame, width=250, fg_color='#F8F1FF')
                    bn_entry.insert(0, record_data[6] if len(record_data) > 6 else "")
                    bn_entry.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["bill_no"] = bn_entry
                    row_num += 1
                
                if c3.get():  # Stent Type
                    customtkinter.CTkLabel(scroll_frame, text="Stent Type", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    st = customtkinter.CTkComboBox(scroll_frame, values=So, width=250, fg_color='#F8F1FF')
                    st.set(record_data[7] if len(record_data) > 7 else "")
                    st.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["stent_type"] = st
                    row_num += 1
                
                if c4.get():  # Stent Size
                    customtkinter.CTkLabel(scroll_frame, text="Stent Size", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    sz_entry = customtkinter.CTkEntry(scroll_frame, width=250, fg_color='#F8F1FF')
                    sz_entry.insert(0, record_data[8] if len(record_data) > 8 else "")
                    sz_entry.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["stent_size"] = sz_entry
                    row_num += 1
                
                if c5.get():  # Batch Number
                    customtkinter.CTkLabel(scroll_frame, text="Batch Number", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    batch_entry = customtkinter.CTkEntry(scroll_frame, width=250, fg_color='#F8F1FF')
                    batch_entry.insert(0, record_data[9] if len(record_data) > 9 else "")
                    batch_entry.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["batch"] = batch_entry
                    row_num += 1
                
                if c6.get():  # Entry Date
                    customtkinter.CTkLabel(scroll_frame, text="Entry Date", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    entry_cal = Calendar(scroll_frame, select="day", font=("", 13))
                    if len(record_data) > 11 and record_data[11]:
                        date_obj = parse_date(record_data[11])
                        if date_obj:
                            try:
                                entry_cal.selection_set(date_obj.date())
                            except:
                                pass
                    entry_cal.grid(row=row_num+1, column=1, sticky=W, padx=10, pady=5)
                    widget_vars["entry_date"] = entry_cal
                    row_num += 1
                
                if c7.get():  # Expiry Date
                    customtkinter.CTkLabel(scroll_frame, text="Expiry Date", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    expiry_cal = Calendar(scroll_frame, select="day", font=("", 13))
                    if len(record_data) > 12 and record_data[12]:
                        date_obj = parse_date(record_data[12])
                        if date_obj:
                            try:
                                expiry_cal.selection_set(date_obj.date())
                            except:
                                pass
                    expiry_cal.grid(row=row_num+1, column=1, sticky=W, padx=10, pady=5)
                    widget_vars["expiry_date"] = expiry_cal
                    row_num += 1
            
            elif file_type == "hospital":
                # Hospital stock fields
                if c1.get():  # Hospital Name
                    customtkinter.CTkLabel(scroll_frame, text="Hospital Name", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    hc = customtkinter.CTkComboBox(scroll_frame, values=Ho, width=250, fg_color='#F8F1FF')
                    hc.set(record_data[0] if len(record_data) > 0 else "")
                    hc.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["hospital"] = hc
                    row_num += 1
                
                if c3.get():  # Stent Type
                    customtkinter.CTkLabel(scroll_frame, text="Stent Type", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    st = customtkinter.CTkComboBox(scroll_frame, values=So, width=250, fg_color='#F8F1FF')
                    st.set(record_data[1] if len(record_data) > 1 else "")
                    st.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["stent_type"] = st
                    row_num += 1
                
                if c4.get():  # Stent Size
                    customtkinter.CTkLabel(scroll_frame, text="Stent Size", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    sz_entry = customtkinter.CTkEntry(scroll_frame, width=250, fg_color='#F8F1FF')
                    sz_entry.insert(0, record_data[2] if len(record_data) > 2 else "")
                    sz_entry.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["stent_size"] = sz_entry
                    row_num += 1
                
                if c5.get():  # Batch Number
                    customtkinter.CTkLabel(scroll_frame, text="Batch Number", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    batch_entry = customtkinter.CTkEntry(scroll_frame, width=250, fg_color='#F8F1FF')
                    batch_entry.insert(0, record_data[3] if len(record_data) > 3 else "")
                    batch_entry.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["batch"] = batch_entry
                    row_num += 1
                
                if c6.get():  # Entry Date
                    customtkinter.CTkLabel(scroll_frame, text="Entry Date", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    entry_cal = Calendar(scroll_frame, select="day", font=("", 13))
                    if len(record_data) > 5 and record_data[5]:
                        date_obj = parse_date(record_data[5])
                        if date_obj:
                            try:
                                entry_cal.selection_set(date_obj.date())
                            except:
                                pass
                    entry_cal.grid(row=row_num+1, column=1, sticky=W, padx=10, pady=5)
                    widget_vars["entry_date"] = entry_cal
                    row_num += 1
                
                if c7.get():  # Expiry Date
                    customtkinter.CTkLabel(scroll_frame, text="Expiry Date", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    expiry_cal = Calendar(scroll_frame, select="day", font=("", 13))
                    if len(record_data) > 6 and record_data[6]:
                        date_obj = parse_date(record_data[6])
                        if date_obj:
                            try:
                                expiry_cal.selection_set(date_obj.date())
                            except:
                                pass
                    expiry_cal.grid(row=row_num+1, column=1, sticky=W, padx=10, pady=5)
                    widget_vars["expiry_date"] = expiry_cal
                    row_num += 1
            
            elif file_type == "office":
                # Office stock fields
                if c3.get():  # Stent Type
                    customtkinter.CTkLabel(scroll_frame, text="Stent Type", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    st = customtkinter.CTkComboBox(scroll_frame, values=So, width=250, fg_color='#F8F1FF')
                    st.set(record_data[0] if len(record_data) > 0 else "")
                    st.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["stent_type"] = st
                    row_num += 1
                
                if c4.get():  # Stent Size
                    customtkinter.CTkLabel(scroll_frame, text="Stent Size", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    sz_entry = customtkinter.CTkEntry(scroll_frame, width=250, fg_color='#F8F1FF')
                    sz_entry.insert(0, record_data[1] if len(record_data) > 1 else "")
                    sz_entry.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["stent_size"] = sz_entry
                    row_num += 1
                
                if c5.get():  # Batch Number
                    customtkinter.CTkLabel(scroll_frame, text="Batch Number", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    batch_entry = customtkinter.CTkEntry(scroll_frame, width=250, fg_color='#F8F1FF')
                    batch_entry.insert(0, record_data[2] if len(record_data) > 2 else "")
                    batch_entry.grid(row=row_num+1, column=1, sticky=W, padx=10)
                    widget_vars["batch"] = batch_entry
                    row_num += 1
                
                if c6.get():  # Entry Date
                    customtkinter.CTkLabel(scroll_frame, text="Entry Date", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    entry_cal = Calendar(scroll_frame, select="day", font=("", 13))
                    if len(record_data) > 4 and record_data[4]:
                        date_obj = parse_date(record_data[4])
                        if date_obj:
                            try:
                                entry_cal.selection_set(date_obj.date())
                            except:
                                pass
                    entry_cal.grid(row=row_num+1, column=1, sticky=W, padx=10, pady=5)
                    widget_vars["entry_date"] = entry_cal
                    row_num += 1
                
                if c7.get():  # Expiry Date
                    customtkinter.CTkLabel(scroll_frame, text="Expiry Date", font=("PT Sans Narrow", 16), anchor=W).grid(row=row_num+1, column=0, padx=10, pady=5, sticky=W)
                    expiry_cal = Calendar(scroll_frame, select="day", font=("", 13))
                    if len(record_data) > 5 and record_data[5]:
                        date_obj = parse_date(record_data[5])
                        if date_obj:
                            try:
                                expiry_cal.selection_set(date_obj.date())
                            except:
                                pass
                    expiry_cal.grid(row=row_num+1, column=1, sticky=W, padx=10, pady=5)
                    widget_vars["expiry_date"] = expiry_cal
                    row_num += 1
            
            # Buttons frame (outside scrollable frame)
            buttons_frame = customtkinter.CTkFrame(update_frame, fg_color="transparent")
            buttons_frame.pack(fill="x", pady=20, padx=10)
            
            save_btn = customtkinter.CTkButton(buttons_frame, text="Save Updates", font=("bold", 15), 
                                               height=40, corner_radius=20, width=200, 
                                               fg_color='#1CAC78', hover_color='#00563B', 
                                               command=save_updates)
            save_btn.pack(side="left", padx=10)
            
            cancel_btn = customtkinter.CTkButton(buttons_frame, text="Cancel", font=("bold", 15), 
                                                 height=40, corner_radius=20, width=200, 
                                                 fg_color='#AB0003', hover_color='#660000', 
                                                 command=homee)
            cancel_btn.pack(side="left", padx=10)
            
            home_btn = customtkinter.CTkButton(buttons_frame, text="Home", font=("bold", 15), 
                                              height=40, corner_radius=20, width=200, 
                                              fg_color='#4fa6f7', hover_color='#3c92e5', 
                                              command=homee)
            home_btn.pack(side="left", padx=10)
            
        if current_view:
            try:
                current_view.destroy()
            except:
                pass
        root1 = customtkinter.CTkFrame(master=content_frame)
        root1.pack(fill="both", expand=True, padx=10, pady=10)
        current_view = root1
        is_loading = False

        # Checkboxes
        c1 = customtkinter.BooleanVar(value=False)
        c2 = customtkinter.BooleanVar(value=False)
        c3 = customtkinter.BooleanVar(value=False) 
        c4 = customtkinter.BooleanVar(value=False)
        c5 = customtkinter.BooleanVar(value=False)
        c6 = customtkinter.BooleanVar(value=False)
        c7 = customtkinter.BooleanVar(value=False)
        c8 = customtkinter.BooleanVar(value=False)
        c9 = customtkinter.BooleanVar(value=False)
        c10 = customtkinter.BooleanVar(value=False)
        c11 = customtkinter.BooleanVar(value=False)
        c12 = customtkinter.BooleanVar(value=False)
        
        # Serial number entry
        customtkinter.CTkLabel(master=root1, text="Serial Number", font=("PT Sans Narrow", 18, "bold")).grid(row=0, column=0, pady=15, padx=10, sticky=W)
        serial_entry = customtkinter.CTkEntry(master=root1, width=300, fg_color='#F8F1FF', font=("PT Sans Narrow", 14))
        serial_entry.grid(row=0, column=1, pady=15, padx=10, sticky=W)
        
        # Checkboxes
        customtkinter.CTkLabel(master=root1, text="Select fields to update:", font=("PT Sans Narrow", 16, "bold")).grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky=W)
        customtkinter.CTkCheckBox(master=root1, text="Hospital Name", variable=c1, onvalue=True, offvalue=False, font=("PT Sans Narrow", 14)).grid(row=2, column=0, columnspan=2, pady=5, padx=20, sticky=W)
        customtkinter.CTkCheckBox(master=root1, text="Doctor Name", variable=c2, onvalue=True, offvalue=False, font=("PT Sans Narrow", 14)).grid(row=3, column=0, columnspan=2, pady=5, padx=20, sticky=W)
        customtkinter.CTkCheckBox(master=root1, text="Stent Type", variable=c3, onvalue=True, offvalue=False, font=("PT Sans Narrow", 14)).grid(row=4, column=0, columnspan=2, pady=5, padx=20, sticky=W)
        customtkinter.CTkCheckBox(master=root1, text="Stent Size", variable=c4, onvalue=True, offvalue=False, font=("PT Sans Narrow", 14)).grid(row=5, column=0, columnspan=2, pady=5, padx=20, sticky=W)
        customtkinter.CTkCheckBox(master=root1, text="Batch Number", variable=c5, onvalue=True, offvalue=False, font=("PT Sans Narrow", 14)).grid(row=6, column=0, columnspan=2, pady=5, padx=20, sticky=W)
        customtkinter.CTkCheckBox(master=root1, text="Entry Date", variable=c6, onvalue=True, offvalue=False, font=("PT Sans Narrow", 14)).grid(row=7, column=0, columnspan=2, pady=5, padx=20, sticky=W)
        customtkinter.CTkCheckBox(master=root1, text="Expiry Date", variable=c7, onvalue=True, offvalue=False, font=("PT Sans Narrow", 14)).grid(row=8, column=0, columnspan=2, pady=5, padx=20, sticky=W)
        customtkinter.CTkCheckBox(master=root1, text="Patient Name", variable=c8, onvalue=True, offvalue=False, font=("PT Sans Narrow", 14)).grid(row=9, column=0, columnspan=2, pady=5, padx=20, sticky=W)
        customtkinter.CTkCheckBox(master=root1, text="Bill Amount", variable=c9, onvalue=True, offvalue=False, font=("PT Sans Narrow", 14)).grid(row=10, column=0, columnspan=2, pady=5, padx=20, sticky=W)
        customtkinter.CTkCheckBox(master=root1, text="I.P.D.", variable=c10, onvalue=True, offvalue=False, font=("PT Sans Narrow", 14)).grid(row=11, column=0, columnspan=2, pady=5, padx=20, sticky=W)
        customtkinter.CTkCheckBox(master=root1, text="Cath Number", variable=c11, onvalue=True, offvalue=False, font=("PT Sans Narrow", 14)).grid(row=12, column=0, columnspan=2, pady=5, padx=20, sticky=W)
        customtkinter.CTkCheckBox(master=root1, text="Bill Number", variable=c12, onvalue=True, offvalue=False, font=("PT Sans Narrow", 14)).grid(row=13, column=0, columnspan=2, pady=5, padx=20, sticky=W)
        
        # Search button
        search_btn = customtkinter.CTkButton(master=root1, text="Search & Update", font=("bold", 15), 
                                             height=40, corner_radius=20, width=200, 
                                             fg_color='#1CAC78', hover_color='#00563B', 
                                             command=search_and_update)
        search_btn.grid(row=14, column=0, pady=20, padx=10)
        
        # Home button
        home_btn = customtkinter.CTkButton(master=root1, text="Home", font=("bold", 15), 
                                           height=40, corner_radius=20, width=200, 
                                           fg_color='#AB0003', hover_color='#660000', 
                                           command=homee)
        home_btn.grid(row=14, column=1, pady=20, padx=10)

    def D():#DATA DELETION
        dialog = customtkinter.CTkInputDialog(text="Type in the Serial Number: ", title="Deletion")
        serial_input = dialog.get_input()
        if not serial_input:
            tkinter.messagebox.showwarning("Warning", "No serial number entered")
            return
        
        b = str(serial_input).strip()
        if not b:
            tkinter.messagebox.showwarning("Warning", "Serial number cannot be empty")
            return
        
        L = None
        base_path = "/Users/apple/Desktop/2nd year/Python Project sem 3/"
        
        # Search in officestock.csv for office stock (6 columns, serial at index 3)
        try:
            f = open(f"{base_path}officestock.csv", "r", errors="ignore")
            r = csv.reader(f)
            for i in r:
                if i and len(i) >= 4:
                    # Check for office stock (6 columns)
                    if len(i) >= 6 and i[3] == b:
                        L = ["office", i]
                        break
                    # Check for used stent (13 columns, serial at index 10)
                    elif len(i) >= 13 and i[10] == b:
                        L = ["stentused", i]
                        break
            f.close()
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Error reading officestock.csv: {str(e)}")
            return
        
        # Search in hospitalstock.csv if not found (7 columns, serial at index 4)
        if not L:
            try:
                f = open(f"{base_path}hospitalstock.csv", "r", errors="ignore")
                r = csv.reader(f)
                for i in r:
                    if i and len(i) >= 5 and i[4] == b:
                        L = ["hospital", i]
                        break
                f.close()
            except Exception as e:
                tkinter.messagebox.showerror("Error", f"Error reading hospitalstock.csv: {str(e)}")
                return
        
        if not L:
            tkinter.messagebox.showerror("Error", f"Serial number {b} not found in any file")
            return

        # Delete the record
        try:
            if L[0] == "office":
                file_path = f"{base_path}officestock.csv"
                temp_path = f"{base_path}n.csv"
                f = open(file_path, "r", errors="ignore")
                n = open(temp_path, "w", newline="", errors="ignore")
                r = csv.reader(f)
                w = csv.writer(n)
                for i in r:
                    if i and len(i) >= 4:
                        if len(i) >= 6 and i[3] != b:  # Office stock
                            w.writerow(i)
                        elif len(i) >= 13 and i[10] != b:  # Used stent
                            w.writerow(i)
                        elif len(i) < 6:  # Keep other entries
                            w.writerow(i)
                    elif i:  # Keep rows that don't meet the length requirement
                        w.writerow(i)
                f.close()
                n.close()
                os.remove(file_path)
                os.rename(temp_path, file_path)
                tkinter.messagebox.showinfo("Deletion", "Entry Deleted Successfully")
                
            elif L[0] == "hospital":
                file_path = f"{base_path}hospitalstock.csv"
                temp_path = f"{base_path}n.csv"
                f = open(file_path, "r", errors="ignore")
                n = open(temp_path, "w", newline="", errors="ignore")
                r = csv.reader(f)
                w = csv.writer(n)
                for i in r:
                    if i and (len(i) < 5 or i[4] != b):
                        w.writerow(i)
                f.close()
                n.close()
                os.remove(file_path)
                os.rename(temp_path, file_path)
                tkinter.messagebox.showinfo("Deletion", "Entry Deleted Successfully")
                
            elif L[0] == "stentused":
                file_path = f"{base_path}stentused.csv"
                temp_path = f"{base_path}n.csv"
                f = open(file_path, "r", errors="ignore")
                n = open(temp_path, "w", newline="", errors="ignore")
                r = csv.reader(f)
                w = csv.writer(n)
                for i in r:
                    if i:
                        # Keep used stents with different serial (serial at index 10)
                        if len(i) < 13 or (len(i) >= 13 and i[10] != b):
                            w.writerow(i)
                f.close()
                n.close()
                os.remove(file_path)
                os.rename(temp_path, file_path)
                tkinter.messagebox.showinfo("Deletion", "Entry Deleted Successfully")
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Failed to delete entry: {str(e)}")
    def FOC():#FOC MARK
        dialog = customtkinter.CTkInputDialog(text="Type in the Serial Number: ", title="FOC")
        serial_input = dialog.get_input()
        if not serial_input:
            tkinter.messagebox.showwarning("Warning", "No serial number entered")
            return
        
        serialno = str(serial_input).strip()
        if not serialno:
            tkinter.messagebox.showwarning("Warning", "Serial number cannot be empty")
            return
        
        base_path = "/Users/apple/Desktop/2nd year/Python Project sem 3/"
        file_path = f"{base_path}officestock.csv"
        temp_path = f"{base_path}b.csv"
        record_found = False
        
        try:
            f = open(file_path, "r", errors="ignore")
            f1 = open(temp_path, "w", newline="", errors="ignore")
            cd = csv.writer(f1)
            cs = csv.reader(f)
            
            for i in cs:
                if i and len(i) > 4:
                    # Check for office stock (6 columns, serial at index 3)
                    if len(i) >= 6 and i[3] == serialno:
                        i[3] = "0"  # Mark as FOC
                        cd.writerow(i)
                        record_found = True
                    else:
                        cd.writerow(i)
                elif i:
                    cd.writerow(i)
            
            f.close()
            f1.close()
            
            if not record_found:
                os.remove(temp_path)
                tkinter.messagebox.showerror("Error", f"Serial number {serialno} not found in office stock")
                return
            
            os.remove(file_path)
            os.rename(temp_path, file_path)
            tkinter.messagebox.showinfo("Success", "FOC marked successfully")
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Failed to mark FOC: {str(e)}")
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
    def REP():#REPORT
        nonlocal current_view, is_loading
        if is_loading:
            return
        is_loading = True
        
        def homee():
            nonlocal current_view, is_loading
            if current_view:
                try:
                    current_view.destroy()
                except:
                    pass
            is_loading = False
            show_dashboard()
        
        base_path = "/Users/apple/Desktop/2nd year/Python Project sem 3/"
        
        # Validation function for file reading
        def validate_and_read_file(file_path, required_columns=None):
            """Validate file exists and has data, return data and status"""
            try:
                if not os.path.exists(file_path):
                    return None, False, f"File not found: {os.path.basename(file_path)}"
                
                f = open(file_path, "r", errors="ignore")
                reader = csv.reader(f)
                data = list(reader)
                f.close()
                
                if not data or len(data) == 0:
                    return None, False, f"No data found in {os.path.basename(file_path)}"
                
                if required_columns:
                    # Check if any row has required columns
                    valid_rows = [row for row in data if row and len(row) >= required_columns]
                    if not valid_rows:
                        return None, False, f"Insufficient columns in {os.path.basename(file_path)}"
                
                return data, True, "Success"
            except Exception as e:
                return None, False, f"Error reading {os.path.basename(file_path)}: {str(e)}"
        
        if current_view:
            try:
                current_view.destroy()
            except:
                pass
        
        root = customtkinter.CTkTabview(master=content_frame)
        root.pack(fill="both", expand=True, padx=10, pady=10)
        current_view = root
        is_loading = False
        
        root1=root.add("Doctor Report")
        root2=root.add("Hospital Report")
        root3=root.add("Doctor Stent Types")
        root4=root.add("Hospital Stent Types")
        root5=root.add("All Stent Types")
        
        # ========== TAB 1: HOSPITAL LIST REPORT ==========
        # Create scrollable frame for tab1
        scroll_frame1 = customtkinter.CTkScrollableFrame(root1)
        scroll_frame1.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header with statistics
        header1 = customtkinter.CTkFrame(scroll_frame1, fg_color="#e8f4f8")
        header1.pack(fill="x", padx=10, pady=10)
        customtkinter.CTkLabel(header1, text="Hospital Names Report", 
                              font=("Helvetica Neue", 20, "bold"), text_color="#1f2a44").pack(pady=10)
        
        # Load and validate data from stentused.csv
        file_path = f"{base_path}stentused.csv"
        data, is_valid, message = validate_and_read_file(file_path, required_columns=13)
        
        if not is_valid:
            error_frame = customtkinter.CTkFrame(scroll_frame1)
            error_frame.pack(fill="both", expand=True, padx=20, pady=20)
            customtkinter.CTkLabel(error_frame, text=f"⚠️ {message}", 
                                  font=("Helvetica Neue", 14), text_color="#dc2626").pack(pady=20)
            b2=customtkinter.CTkButton(root1,text="Home",font=("bold",15),height=40,corner_radius=20,width=200,command=homee,fg_color='#AB0003',hover_color='#660000').pack(pady=10)
        else:
            # Collect unique hospital names
            hospitals_set = set()
            for k in data:
                if k and len(k) >= 13:
                    hospital = k[1].strip() if len(k) > 1 else ""
                    if hospital and hospital != "":
                        hospitals_set.add(hospital)
            
            # Convert to sorted list
            hospitals_list = sorted(list(hospitals_set))
            
            # Statistics frame
            stats_frame1 = customtkinter.CTkFrame(scroll_frame1, fg_color="#f0f9ff")
            stats_frame1.pack(fill="x", padx=10, pady=10)
            stats_text1 = f"🏥 Total Unique Hospitals: {len(hospitals_list)}"
            customtkinter.CTkLabel(stats_frame1, text=stats_text1, 
                                  font=("Helvetica Neue", 14, "bold"), text_color="#1e40af").pack(pady=10)
            
            # Data table - Only Hospital Names
            table_frame1 = customtkinter.CTkFrame(scroll_frame1)
            table_frame1.pack(fill="both", expand=True, padx=10, pady=10)
            customtkinter.CTkLabel(table_frame1, text="List of All Hospitals", 
                                  font=("Helvetica Neue", 16, "bold")).pack(pady=10)
            
            tree1 = ttk.Treeview(table_frame1, columns=("Hospital",), show='headings', height=15)
            tree1.column("#1", width=600)
            tree1.heading("Hospital", text="Hospital Name")
            
            for hospital in hospitals_list:
                tree1.insert('', END, values=(hospital,))
            
            tree1.pack(fill="both", expand=True, padx=10, pady=10)
        
        b2=customtkinter.CTkButton(root1,text="Home",font=("bold",15),height=40,corner_radius=20,width=200,command=homee,fg_color='#AB0003',hover_color='#660000').pack(pady=10)
        
        # ========== TAB 2: HOSPITAL REPORT ==========
        scroll_frame2 = customtkinter.CTkScrollableFrame(root2)
        scroll_frame2.pack(fill="both", expand=True, padx=10, pady=10)
        
        header2 = customtkinter.CTkFrame(scroll_frame2, fg_color="#fef3c7")
        header2.pack(fill="x", padx=10, pady=10)
        customtkinter.CTkLabel(header2, text="Hospital-Doctor Relationship Report", 
                              font=("Helvetica Neue", 20, "bold"), text_color="#1f2a44").pack(pady=10)
        
        data, is_valid, message = validate_and_read_file(file_path, required_columns=13)
        
        if not is_valid:
            error_frame = customtkinter.CTkFrame(scroll_frame2)
            error_frame.pack(fill="both", expand=True, padx=20, pady=20)
            customtkinter.CTkLabel(error_frame, text=f"⚠️ {message}", 
                                  font=("Helvetica Neue", 14), text_color="#dc2626").pack(pady=20)
        else:
            H = {}
            hospital_count = {}
            for k in data:
                if k and len(k) >= 13:
                    doctor = k[0].strip()
                    hospital = k[1].strip()
                    if doctor and hospital and doctor != "" and hospital != "":
                        if hospital not in H:
                            H[hospital] = []
                            hospital_count[hospital] = 0
                        if doctor not in H[hospital]:
                            H[hospital].append(doctor)
                        hospital_count[hospital] += 1
            
            stats_frame2 = customtkinter.CTkFrame(scroll_frame2, fg_color="#f0f9ff")
            stats_frame2.pack(fill="x", padx=10, pady=10)
            stats_text2 = f"🏥 Total Hospitals: {len(H)} | Total Records: {sum(hospital_count.values())}"
            customtkinter.CTkLabel(stats_frame2, text=stats_text2, 
                                  font=("Helvetica Neue", 14, "bold"), text_color="#1e40af").pack(pady=10)
            
            graph_frame2 = customtkinter.CTkFrame(scroll_frame2, fg_color="#ffffff")
            graph_frame2.pack(fill="both", expand=True, padx=10, pady=10)
            
            if H and hospital_count:
                fig2 = Figure(figsize=(8, 4), dpi=100, facecolor='white')
                ax2 = fig2.add_subplot(111)
                
                sorted_hospitals = sorted(hospital_count.items(), key=lambda x: x[1], reverse=True)[:10]
                hospitals = [h[0] for h in sorted_hospitals]
                counts = [h[1] for h in sorted_hospitals]
                
                colors2 = plt.cm.Pastel1(range(len(hospitals)))
                bars = ax2.bar(hospitals, counts, color=colors2, edgecolor='white', linewidth=1.5)
                ax2.set_xlabel('Hospital Name', fontsize=12, fontweight='bold')
                ax2.set_ylabel('Number of Stents Used', fontsize=12, fontweight='bold')
                ax2.set_title('Top 10 Hospitals by Stent Usage', fontsize=14, fontweight='bold', pad=15)
                ax2.grid(axis='y', alpha=0.3, linestyle='--')
                plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
                
                for bar, val in zip(bars, counts):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + max(counts) * 0.01,
                            f'{int(val)}', ha='center', va='bottom', fontweight='bold', fontsize=9)
                
                fig2.tight_layout()
                canvas2 = FigureCanvasTkAgg(fig2, master=graph_frame2)
                canvas2.draw()
                canvas2.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
            table_frame2 = customtkinter.CTkFrame(scroll_frame2)
            table_frame2.pack(fill="both", expand=True, padx=10, pady=10)
            customtkinter.CTkLabel(table_frame2, text="Detailed Hospital-Doctor Mapping", 
                                  font=("Helvetica Neue", 16, "bold")).pack(pady=10)
            
            tree2 = ttk.Treeview(table_frame2, columns=("Name", "Doctor", "Count"), show='headings', height=10)
            tree2.column("#1", width=300)
            tree2.column("#2", width=400)
            tree2.column("#3", width=150)
            tree2.heading("Name", text="Hospital Name")
            tree2.heading("Doctor", text="Doctor Names")
            tree2.heading("Count", text="Stents Used")
            
            for hospital in sorted(H.keys()):
                doctors = ", ".join(sorted(set(H[hospital])))
                count = hospital_count.get(hospital, 0)
                tree2.insert('', END, values=(hospital, doctors, count))
            
            tree2.pack(fill="both", expand=True, padx=10, pady=10)
        
        b2=customtkinter.CTkButton(root2,text="Home",font=("bold",15),height=40,corner_radius=20,width=200,command=homee,fg_color='#AB0003',hover_color='#660000').pack(pady=10)
        
        # ========== TAB 3: DOCTOR STENT TYPES ==========
        scroll_frame3 = customtkinter.CTkScrollableFrame(root3)
        scroll_frame3.pack(fill="both", expand=True, padx=10, pady=10)
        
        header3 = customtkinter.CTkFrame(scroll_frame3, fg_color="#dcfce7")
        header3.pack(fill="x", padx=10, pady=10)
        customtkinter.CTkLabel(header3, text="Stent Types Used by Doctors", 
                              font=("Helvetica Neue", 20, "bold"), text_color="#1f2a44").pack(pady=10)
        
        data, is_valid, message = validate_and_read_file(file_path, required_columns=13)
        
        if not is_valid:
            error_frame = customtkinter.CTkFrame(scroll_frame3)
            error_frame.pack(fill="both", expand=True, padx=20, pady=20)
            customtkinter.CTkLabel(error_frame, text=f"⚠️ {message}", 
                                  font=("Helvetica Neue", 14), text_color="#dc2626").pack(pady=20)
        else:
            D_stents = {}
            stent_type_counts = {}
            for k in data:
                if k and len(k) >= 13:
                    doctor = k[0].strip()
                    stent_type = k[7].strip() if len(k) > 7 else ""
                    if doctor and stent_type and doctor != "" and stent_type != "":
                        if doctor not in D_stents:
                            D_stents[doctor] = []
                        if stent_type not in D_stents[doctor]:
                            D_stents[doctor].append(stent_type)
                        stent_type_counts[stent_type] = stent_type_counts.get(stent_type, 0) + 1
            
            stats_frame3 = customtkinter.CTkFrame(scroll_frame3, fg_color="#f0f9ff")
            stats_frame3.pack(fill="x", padx=10, pady=10)
            stats_text3 = f"👨‍⚕️ Total Doctors: {len(D_stents)} | Unique Stent Types: {len(stent_type_counts)}"
            customtkinter.CTkLabel(stats_frame3, text=stats_text3, 
                                  font=("Helvetica Neue", 14, "bold"), text_color="#1e40af").pack(pady=10)
            
            graph_frame3 = customtkinter.CTkFrame(scroll_frame3, fg_color="#ffffff")
            graph_frame3.pack(fill="both", expand=True, padx=10, pady=10)
            
            if stent_type_counts:
                fig3 = Figure(figsize=(8, 4), dpi=100, facecolor='white')
                ax3 = fig3.add_subplot(111)
                
                sorted_stents = sorted(stent_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                stents = [s[0] for s in sorted_stents]
                counts = [s[1] for s in sorted_stents]
                
                colors3 = plt.cm.viridis(np.linspace(0, 1, len(stents)))
                bars = ax3.barh(stents, counts, color=colors3, edgecolor='white', linewidth=1.5)
                ax3.set_xlabel('Usage Count', fontsize=12, fontweight='bold')
                ax3.set_ylabel('Stent Type', fontsize=12, fontweight='bold')
                ax3.set_title('Top 10 Most Used Stent Types', fontsize=14, fontweight='bold', pad=15)
                ax3.grid(axis='x', alpha=0.3, linestyle='--')
                
                for bar, val in zip(bars, counts):
                    width = bar.get_width()
                    ax3.text(width + max(counts) * 0.01, bar.get_y() + bar.get_height()/2,
                            f'{int(val)}', ha='left', va='center', fontweight='bold', fontsize=9)
                
                fig3.tight_layout()
                canvas3 = FigureCanvasTkAgg(fig3, master=graph_frame3)
                canvas3.draw()
                canvas3.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
            table_frame3 = customtkinter.CTkFrame(scroll_frame3)
            table_frame3.pack(fill="both", expand=True, padx=10, pady=10)
            customtkinter.CTkLabel(table_frame3, text="Doctor-Stent Type Mapping", 
                                  font=("Helvetica Neue", 16, "bold")).pack(pady=10)
            
            tree3 = ttk.Treeview(table_frame3, columns=("Name", "Stent Types"), show='headings', height=10)
            tree3.column("#1", width=300)
            tree3.column("#2", width=500)
            tree3.heading("Name", text="Doctor Name")
            tree3.heading("Stent Types", text="Stent Types Used")
            
            for doctor in sorted(D_stents.keys()):
                stents = ", ".join(sorted(set(D_stents[doctor])))
                tree3.insert('', END, values=(doctor, stents))
            
            tree3.pack(fill="both", expand=True, padx=10, pady=10)
        
        b2=customtkinter.CTkButton(root3,text="Home",font=("bold",15),height=40,corner_radius=20,width=200,command=homee,fg_color='#AB0003',hover_color='#660000').pack(pady=10)
        
        # ========== TAB 4: HOSPITAL STENT TYPES ==========
        scroll_frame4 = customtkinter.CTkScrollableFrame(root4)
        scroll_frame4.pack(fill="both", expand=True, padx=10, pady=10)
        
        header4 = customtkinter.CTkFrame(scroll_frame4, fg_color="#fce7f3")
        header4.pack(fill="x", padx=10, pady=10)
        customtkinter.CTkLabel(header4, text="Stent Types Used in Hospitals", 
                              font=("Helvetica Neue", 20, "bold"), text_color="#1f2a44").pack(pady=10)
        
        H_stents = {}
        hospital_stent_counts = {}
        
        # Read from stentused.csv (used stents)
        used_stent_file = f"{base_path}stentused.csv"
        data, is_valid, message = validate_and_read_file(used_stent_file, required_columns=13)
        if is_valid:
            for k in data:
                if k and len(k) >= 13:
                    hospital = k[1].strip()
                    stent_type = k[7].strip() if len(k) > 7 else ""
                    if hospital and stent_type and hospital != "" and stent_type != "":
                        if hospital not in H_stents:
                            H_stents[hospital] = []
                        if stent_type not in H_stents[hospital]:
                            H_stents[hospital].append(stent_type)
                        key = f"{hospital}_{stent_type}"
                        hospital_stent_counts[key] = hospital_stent_counts.get(key, 0) + 1
        
        # Read from hospitalstock.csv
        hospital_file = f"{base_path}hospitalstock.csv"
        hospital_data, is_valid_h, message_h = validate_and_read_file(hospital_file, required_columns=7)
        if is_valid_h:
            for k in hospital_data:
                if k and len(k) >= 7:
                    hospital = k[0].strip()
                    stent_type = k[1].strip()
                    if hospital and stent_type and hospital != "" and stent_type != "":
                        if hospital not in H_stents:
                            H_stents[hospital] = []
                        if stent_type not in H_stents[hospital]:
                            H_stents[hospital].append(stent_type)
                        key = f"{hospital}_{stent_type}"
                        hospital_stent_counts[key] = hospital_stent_counts.get(key, 0) + 1
        
        if H_stents:
            stats_frame4 = customtkinter.CTkFrame(scroll_frame4, fg_color="#f0f9ff")
            stats_frame4.pack(fill="x", padx=10, pady=10)
            total_stent_types = sum(len(stents) for stents in H_stents.values())
            stats_text4 = f"🏥 Total Hospitals: {len(H_stents)} | Total Stent Type Entries: {total_stent_types}"
            customtkinter.CTkLabel(stats_frame4, text=stats_text4, 
                                  font=("Helvetica Neue", 14, "bold"), text_color="#1e40af").pack(pady=10)
            
            graph_frame4 = customtkinter.CTkFrame(scroll_frame4, fg_color="#ffffff")
            graph_frame4.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Count stent types per hospital
            hospital_stent_counts_bar = {h: len(stents) for h, stents in H_stents.items()}
            if hospital_stent_counts_bar:
                fig4 = Figure(figsize=(8, 4), dpi=100, facecolor='white')
                ax4 = fig4.add_subplot(111)
                
                sorted_hospitals = sorted(hospital_stent_counts_bar.items(), key=lambda x: x[1], reverse=True)[:10]
                hospitals = [h[0] for h in sorted_hospitals]
                counts = [h[1] for h in sorted_hospitals]
                
                colors4 = plt.cm.coolwarm(np.linspace(0, 1, len(hospitals)))
                bars = ax4.bar(hospitals, counts, color=colors4, edgecolor='white', linewidth=1.5)
                ax4.set_xlabel('Hospital Name', fontsize=12, fontweight='bold')
                ax4.set_ylabel('Number of Stent Types', fontsize=12, fontweight='bold')
                ax4.set_title('Hospitals by Stent Type Variety', fontsize=14, fontweight='bold', pad=15)
                ax4.grid(axis='y', alpha=0.3, linestyle='--')
                plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
                
                for bar, val in zip(bars, counts):
                    height = bar.get_height()
                    ax4.text(bar.get_x() + bar.get_width()/2., height + max(counts) * 0.01,
                            f'{int(val)}', ha='center', va='bottom', fontweight='bold', fontsize=9)
                
                fig4.tight_layout()
                canvas4 = FigureCanvasTkAgg(fig4, master=graph_frame4)
                canvas4.draw()
                canvas4.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
            table_frame4 = customtkinter.CTkFrame(scroll_frame4)
            table_frame4.pack(fill="both", expand=True, padx=10, pady=10)
            customtkinter.CTkLabel(table_frame4, text="Hospital-Stent Type Mapping", 
                                  font=("Helvetica Neue", 16, "bold")).pack(pady=10)
            
            tree4 = ttk.Treeview(table_frame4, columns=("Name", "Stent Types", "Count"), show='headings', height=10)
            tree4.column("#1", width=300)
            tree4.column("#2", width=400)
            tree4.column("#3", width=100)
            tree4.heading("Name", text="Hospital Name")
            tree4.heading("Stent Types", text="Stent Types")
            tree4.heading("Count", text="Count")
            
            for hospital in sorted(H_stents.keys()):
                stents = ", ".join(sorted(set(H_stents[hospital])))
                count = len(H_stents[hospital])
                tree4.insert('', END, values=(hospital, stents, count))
            
            tree4.pack(fill="both", expand=True, padx=10, pady=10)
        else:
            error_frame = customtkinter.CTkFrame(scroll_frame4)
            error_frame.pack(fill="both", expand=True, padx=20, pady=20)
            customtkinter.CTkLabel(error_frame, text="⚠️ No hospital-stent data available", 
                                  font=("Helvetica Neue", 14), text_color="#dc2626").pack(pady=20)
        
        b2=customtkinter.CTkButton(root4,text="Home",font=("bold",15),height=40,corner_radius=20,width=200,command=homee,fg_color='#AB0003',hover_color='#660000').pack(pady=10)
        
        # ========== TAB 5: ALL STENT TYPES ==========
        scroll_frame5 = customtkinter.CTkScrollableFrame(root5)
        scroll_frame5.pack(fill="both", expand=True, padx=10, pady=10)
        
        header5 = customtkinter.CTkFrame(scroll_frame5, fg_color="#e0e7ff")
        header5.pack(fill="x", padx=10, pady=10)
        customtkinter.CTkLabel(header5, text="All Available Stent Types", 
                              font=("Helvetica Neue", 20, "bold"), text_color="#1f2a44").pack(pady=10)
        
        dets_file = f"{base_path}Dets.csv"
        data_dets, is_valid_dets, message_dets = validate_and_read_file(dets_file)
        
        if not is_valid_dets:
            error_frame = customtkinter.CTkFrame(scroll_frame5)
            error_frame.pack(fill="both", expand=True, padx=20, pady=20)
            customtkinter.CTkLabel(error_frame, text=f"⚠️ {message_dets}", 
                                  font=("Helvetica Neue", 14), text_color="#dc2626").pack(pady=20)
        else:
            So = []
            for i in data_dets:
                if i and len(i) > 2 and i[2] != "":
                    So.append(i[2].strip())
            
            unique_stents = sorted(set([s for s in So if s and s.strip() != ""]))
            
            stats_frame5 = customtkinter.CTkFrame(scroll_frame5, fg_color="#f0f9ff")
            stats_frame5.pack(fill="x", padx=10, pady=10)
            stats_text5 = f"📋 Total Unique Stent Types: {len(unique_stents)}"
            customtkinter.CTkLabel(stats_frame5, text=stats_text5, 
                                  font=("Helvetica Neue", 14, "bold"), text_color="#1e40af").pack(pady=10)
            
            # Pie chart for stent type distribution (if we have usage data)
            graph_frame5 = customtkinter.CTkFrame(scroll_frame5, fg_color="#ffffff")
            graph_frame5.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Count usage of each stent type from officestock
            data, is_valid, message = validate_and_read_file(file_path, required_columns=13)
            stent_usage = {}
            if is_valid:
                for k in data:
                    if k and len(k) >= 13:
                        stent_type = k[7].strip() if len(k) > 7 else ""
                        if stent_type and stent_type != "":
                            stent_usage[stent_type] = stent_usage.get(stent_type, 0) + 1
            
            if stent_usage:
                fig5 = Figure(figsize=(8, 5), dpi=100, facecolor='white')
                ax5 = fig5.add_subplot(111)
                
                # Get top 10 most used
                sorted_usage = sorted(stent_usage.items(), key=lambda x: x[1], reverse=True)[:10]
                labels = [s[0] for s in sorted_usage]
                sizes = [s[1] for s in sorted_usage]
                
                colors5 = plt.cm.tab20(range(len(labels)))
                explode = [0.05] * len(labels)
                
                wedges, texts, autotexts = ax5.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                                   colors=colors5, explode=explode, startangle=90,
                                                   textprops={'fontsize': 9})
                ax5.set_title('Top 10 Stent Types Usage Distribution', fontsize=14, fontweight='bold', pad=15)
                
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                fig5.tight_layout()
                canvas5 = FigureCanvasTkAgg(fig5, master=graph_frame5)
                canvas5.draw()
                canvas5.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            
            table_frame5 = customtkinter.CTkFrame(scroll_frame5)
            table_frame5.pack(fill="both", expand=True, padx=10, pady=10)
            customtkinter.CTkLabel(table_frame5, text="Complete Stent Types List", 
                                  font=("Helvetica Neue", 16, "bold")).pack(pady=10)
            
            tree5 = ttk.Treeview(table_frame5, columns=("Sno", "Stent", "Usage"), show='headings', height=10)
            tree5.column("#1", width=100)
            tree5.column("#2", width=500)
            tree5.column("#3", width=150)
            tree5.heading("Sno", text="S.No.")
            tree5.heading("Stent", text="Stent Type")
            tree5.heading("Usage", text="Times Used")
            
            c = 1
            for k in unique_stents:
                usage_count = stent_usage.get(k, 0)
                tree5.insert('', END, values=(c, k, usage_count))
                c += 1
            
            tree5.pack(fill="both", expand=True, padx=10, pady=10)
        
        b2=customtkinter.CTkButton(root5,text="Home",font=("bold",15),height=40,corner_radius=20,width=200,command=homee,fg_color='#AB0003',hover_color='#660000').pack(pady=10)
    def IN():#INVOICE
        nonlocal current_view, is_loading
        if is_loading:
            return
        is_loading = True
        
        f=open("/Users/apple/Desktop/2nd year/Python Project sem 3/Dets.csv","r")
        r=csv.reader(f)
        #f.close()
        Ho=[]
        for i in r:
            if i and len(i) > 1 and i[1]!="":
                Ho.append(i[1].strip())
        f.close()
        # Remove duplicates while preserving order
        Ho = list(dict.fromkeys(Ho))
        def homee():
            nonlocal current_view, is_loading
            if current_view:
                try:
                    current_view.destroy()
                except:
                    pass
            is_loading = False
            show_dashboard()
        def ent():

            IN=e1.get()
            PN=e2.get()
            ST=e3.get()
            DN=e4.get()
            A=e5.get()
            L=[IN,PN,ST,DN,A]
            f=open("Invoice.csv","a")
            w=csv.writer(f)
            w.writerow(L)
            f.close()
            tkinter.messagebox.showinfo("Entry Page", "Entry Registered Successfully")




        if current_view:
            try:
                current_view.destroy()
            except:
                pass
        root = customtkinter.CTkFrame(master=content_frame)
        root.pack(fill="both", expand=True, padx=10, pady=10)
        current_view = root
        is_loading = False

        i=customtkinter.CTkLabel(root,text="Invoice Number",font=("PT Sans Narrow",20),anchor=W).grid(row=0,column=0,padx=10,pady=10)
        e1=customtkinter.CTkEntry(root,width=250,fg_color='#F8F1FF')
        e1.bind('<Return>', go_to_next_element)
        e1.grid(row=0,column=1,sticky=W)

        pn=customtkinter.CTkLabel(root,text="Patient Name",font=("PT Sans Narrow",20),anchor=W).grid(row=1,column=0,padx=10,pady=10)
        e2=customtkinter.CTkEntry(root,width=250,fg_color='#F8F1FF')
        e2.bind('<Return>', go_to_next_element)
        e2.grid(row=1,column=1,sticky=W)

        st=customtkinter.CTkLabel(root,text="Stent Type",font=("PT Sans Narrow",20),anchor=W).grid(row=2,column=0,padx=10,pady=10)
        e3=customtkinter.CTkEntry(root,width=250,fg_color='#F8F1FF')
        e3.bind('<Return>', go_to_next_element)
        e3.grid(row=2,column=1,sticky=W)

        bm=customtkinter.CTkLabel(root,text="Doctor Name",font=("PT Sans Narrow",20),anchor=W).grid(row=3,column=0,padx=10,pady=10)
        e4=customtkinter.CTkComboBox(root,values=Ho,width=250,fg_color='#F8F1FF')

        e4.bind('<Return>', go_to_next_element)
        e4.grid(row=3,column=1,sticky=W)

        ip=customtkinter.CTkLabel(root,text="Amount",font=("PT Sans Narrow",20),anchor=W).grid(row=4,column=0,padx=10,pady=10)
        e5=customtkinter.CTkEntry(root,width=250,fg_color='#F8F1FF')
        e5.bind('<Return>', go_to_next_element)
        e5.grid(row=4,column=1,sticky=W,padx=5)

        b1=customtkinter.CTkButton(master=root,text="Enter Data",font=("bold",15),height=40,corner_radius=20,width=200,fg_color='#1CAC78',hover_color='#00563B',command=ent).grid(row=5,column=0,pady=10)
        b2=customtkinter.CTkButton(master=root,text="Home",font=("bold",15),height=40,corner_radius=20,width=200,command=homee,fg_color='#AB0003',hover_color='#660000').grid(row=5,column=1) 
    # Create main window
    H=customtkinter.CTk()
    try:
        H.iconbitmap('/Users/apple/Desktop/2nd year/Python Project sem 3/cv-3.ico')
    except:
        pass  # Icon file might not exist
    H.state('zoomed')
    H.configure(fg_color='#f5f7fa')
    H.title("Stent Management System")
    
    # Professional color theme
    SIDEBAR_BG = "#1e293b"  # Dark slate
    SIDEBAR_ACTIVE = "#3b82f6"  # Blue
    SIDEBAR_HOVER = "#475569"  # Slate
    CONTENT_BG = "#f8fafc"  # Light gray
    
    # Create sidebar
    sidebar = customtkinter.CTkFrame(H, width=280, corner_radius=0, fg_color=SIDEBAR_BG, border_width=0)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)
    
    # Logo section
    logo_frame = customtkinter.CTkFrame(sidebar, fg_color="transparent")
    logo_frame.pack(fill="x", padx=15, pady=(25, 20))
    
    try:
        # Try to load logo image using CTkImage for customtkinter compatibility
        logo_image = Image.open("/Users/apple/Desktop/2nd year/Python Project sem 3/bv-2.jpeg")
        logo_image = logo_image.resize((60, 60), Image.Resampling.LANCZOS)
        logo_ctk = CTkImage(light_image=logo_image, dark_image=logo_image, size=(140, 140))
        logo_label = customtkinter.CTkLabel(
            logo_frame,
            image=logo_ctk,
            text=""
        )
        logo_label.pack(pady=(0, 10))
    except Exception as e:
        # If logo not found, use text logo
        logo_label = customtkinter.CTkLabel(
            logo_frame,
            text="⚕️",
            font=("Helvetica Neue", 40),
            text_color="#ffffff"
        )
        logo_label.pack(pady=(0, 10))
    
    # Sidebar title
    sidebar_title = customtkinter.CTkLabel(
        logo_frame,
        text="Stent Management",
        font=("Helvetica Neue", 20, "bold"),
        text_color="#ffffff"
    )
    sidebar_title.pack()
    
    subtitle = customtkinter.CTkLabel(
        logo_frame,
        text="Inventory System",
        font=("Helvetica Neue", 12),
        text_color="#94a3b8"
    )
    subtitle.pack(pady=(2, 0))
    
    # Separator
    separator = customtkinter.CTkFrame(sidebar, height=1, fg_color="#334155")
    separator.pack(fill="x", padx=20, pady=(15, 20))
    
    # Sidebar buttons
    active_button = [None]  # Track active button
    
    def set_active_button(btn):
        if active_button[0]:
            active_button[0].configure(fg_color=SIDEBAR_BG, text_color="#cbd5e1")
        btn.configure(fg_color=SIDEBAR_ACTIVE, text_color="#ffffff")
        active_button[0] = btn
    
    def create_sidebar_btn(text, icon, command):
        def guarded_command():
            nonlocal is_loading
            if is_loading:
                return  # Prevent multiple simultaneous loads
            set_active_button(btn)
            try:
                command()
            except Exception as e:
                print(f"Error executing command: {e}")
        
        btn = customtkinter.CTkButton(
            sidebar,
            text=f"{icon}  {text}",
            command=guarded_command,
            font=("Helvetica Neue", 18),
            width=240,
            height=50,
            corner_radius=12,
            fg_color=SIDEBAR_BG,
            hover_color=SIDEBAR_HOVER,
            text_color="#cbd5e1",
            anchor="w",
            border_width=0
        )
        btn.pack(pady=4, padx=20)
        return btn
    
    # Create sidebar buttons - Dashboard first, then Data Entry
    dashboard_btn = create_sidebar_btn("Dashboard", "📊", show_dashboard)
    set_active_button(dashboard_btn)  # Dashboard is default active
    
    create_sidebar_btn("Data Entry", "📝", DE)
    create_sidebar_btn("Data Updation", "🔄", DU)
    create_sidebar_btn("Stent Used", "🏥", SU)
    create_sidebar_btn("Entry of Invoice", "📄", IN)
    create_sidebar_btn("Report", "📈", REP)
    create_sidebar_btn("Free of Cost", "🎁", FOC)
    create_sidebar_btn("Data Deletion", "🗑️", D)
    
    # Footer section
    footer_frame = customtkinter.CTkFrame(sidebar, fg_color="transparent")
    footer_frame.pack(fill="x", padx=20, pady=(10, 20))
    
    separator2 = customtkinter.CTkFrame(sidebar, height=1, fg_color="#334155")
    separator2.pack(fill="x", padx=20, pady=(0, 15))
    
    footer_label = customtkinter.CTkLabel(
        footer_frame,
        text="© 2025 Stent Management",
        font=("Helvetica Neue", 10),
        text_color="#64748b"
    )
    footer_label.pack()
    
    # Create content area
    content_frame = customtkinter.CTkFrame(H, fg_color=CONTENT_BG)
    content_frame.pack(side="right", fill="both", expand=True)
    
    # Show dashboard by default
    show_dashboard()
    
    H.mainloop()


# LOGIN PAGE
def new():
    def en():#ENTREING NEW USERNAME
        e1 = Entrr1.get()
        e2 = Entrr2.get()
        e3 = Entrr3.get()
        x = 0
        if e1 == "" or (e2 == "" or e3 == ""):
            tkinter.messagebox.showinfo('Error', 'Enter all the values in!')
            
        elif e2 != e3:
            tkinter.messagebox.showinfo('Error', 'Passwords do not match')
        else:
            F=open("/Users/apple/Desktop/2nd year/Python Project sem 3/Password1.bin","ab")
            p.dump([e1,e2],F)
            F.close()
            tkinter.messagebox.showinfo('Login', 'Logged in Successfully')
            top.destroy()
            HB()

    Entr1.destroy()
    Entr2.destroy()
    Buttn1.destroy()

    Entrr1 = customtkinter.CTkEntry(master=t1,placeholder_text="Username")
    Entrr1.bind('<Return>', go_to_next_element)
    Entrr1.pack(pady=5,padx=20)

    Entrr2 = customtkinter.CTkEntry(master=t1,placeholder_text="Password")
    Entrr2.bind('<Return>',go_to_next_element)
    Entrr2.configure(show="*")
    Entrr2.pack(pady=5)

    def entry_3_return_key_event(event):
        en()
    Entrr3 = customtkinter.CTkEntry(master=t1,placeholder_text="Re-Password")
    Entrr3.bind('<Return>',entry_3_return_key_event)
    Entrr3.configure(show="*")
    Entrr3.pack(pady=5)

    Buttnn1 = customtkinter.CTkButton(master=t1,text="Submit", command=en)
    Buttnn1.pack(pady=5)
def Log():
    e1 = Entr1.get().strip()
    e2 = Entr2.get().strip()
    if e1 == "" or e2 == "":
        tkinter.messagebox.showinfo('Error', 'Enter all the values in!')
        return
    
    file_path = '/Users/apple/Desktop/2nd year/Python Project sem 3/Password1.bin'
    if not os.path.exists(file_path):
        tkinter.messagebox.showerror('Error', 'Password file not found. Please register first.')
        return
    
    try:
        F = open(file_path, 'rb')
        found = False
        try:
            while True:
                g = p.load(F)
                if g[0] == e1 and g[1] == e2:
                    tkinter.messagebox.showinfo('Register', 'Enter new Username & password')
                    F.close()
                    new()
                    found = True
                    break
        except EOFError:
            F.close()
            if not found:
                tkinter.messagebox.showerror('Error', 'Enter Correct ID Password')
        except Exception as e:
            F.close()
            tkinter.messagebox.showerror('Error', f'Error reading password file: {str(e)}')
    except Exception as e:
        tkinter.messagebox.showerror('Error', f'Failed to open password file: {str(e)}')

def Login():
    e1 = Entry1.get().strip()
    e2 = Entry2.get().strip()
    if e1 == "" or e2 == "":
        tkinter.messagebox.showinfo('Error', 'Enter all the values in!')
        return
    
    file_path = '/Users/apple/Desktop/2nd year/Python Project sem 3/Password1.bin'
    if not os.path.exists(file_path):
        tkinter.messagebox.showerror('Error', 'Password file not found. Please register first.')
        return
    
    try:
        F = open(file_path, 'rb')
        found = False
        try:
            while True:
                g = p.load(F)
                if g[0] == e1 and g[1] == e2:
                    F.close()
                    tkinter.messagebox.showinfo('Login', 'Logged in Successfully')
                    top.destroy()
                    HB()
                    found = True
                    break
        except EOFError:
            F.close()
            if not found:
                tkinter.messagebox.showerror('Login', 'Enter Correct ID Password')
        except Exception as e:
            F.close()
            tkinter.messagebox.showerror('Error', f'Error reading password file: {str(e)}')
    except Exception as e:
        tkinter.messagebox.showerror('Error', f'Failed to open password file: {str(e)}')


top = customtkinter.CTk()
try:
    icon_path = '/Users/apple/Desktop/2nd year/Python Project sem 3/cv-3.ico'
    if os.path.exists(icon_path):
        top.iconbitmap(icon_path)
except:
    pass  # Continue if icon file doesn't exist


top.configure(fg_color='#ffffff')
top.geometry("320x300")
top.title("Registration & Login Page")
mt=customtkinter.CTkTabview(top,height=250,width=250,corner_radius=20)

mt.pack(pady=15)

t1=mt.add("Register")
t2=mt.add("Login")
mt.set("Login")

Entry1 = customtkinter.CTkEntry(master=t2,placeholder_text="Username")
Entry1.bind('<Return>', go_to_next_element)
Entry1.pack(pady=5)

def entry_1_return_key_event(event):
    Login()
Entry2 = customtkinter.CTkEntry(master=t2,placeholder_text="Password")
Entry2.bind('<Return>',entry_1_return_key_event)
Entry2.configure(show="*")
Entry2.pack(pady=5)

Button1 = customtkinter.CTkButton(master=t2,text="Submit", command=Login)
Button1.pack(pady=5)


Entr1 = customtkinter.CTkEntry(master=t1,placeholder_text="ID")
Entr1.bind('<Return>', go_to_next_element)
Entr1.pack(pady=5)

def entry_2_return_key_event(event):
    Log()
Entr2 = customtkinter.CTkEntry(master=t1,placeholder_text="Password")
Entr2.bind('<Return>',entry_2_return_key_event)
Entr2.configure(show="*")
Entr2.pack(pady=5)

Buttn1 = customtkinter.CTkButton(master=t1,text="Submit",command=Log)
Buttn1.pack(pady=5)

#Scaling
screen_width = top.winfo_screenwidth()
screen_height = top.winfo_screenheight()
y=0.5625
    
x=screen_height/screen_width
z=y/x
customtkinter.set_widget_scaling(z)  
customtkinter.set_window_scaling(z)

top.mainloop()




