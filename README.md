# Medical Stent Inventory Management System

A desktop application built with **Python** and **Tkinter** to manage medical stent inventory across hospitals. The system handles stock tracking, stent usage records, billing, expiry monitoring, and analytics — all backed by CSV-based storage.

---

## Project Info

| Field | Details |
|---|---|
| **Course** | Python Project — Semester 3 |
| **Batch** | L076 |
| **Language** | Python 3 |
| **UI Framework** | Tkinter + CustomTkinter |

---

## Features

### Authentication
- Secure login with username and password stored in a binary file using Python's `pickle` module
- New user registration with password confirmation

### Dashboard
- Summary cards: Last Usage Date, Earliest Expiry Date
- Bar chart: Stents used per hospital (all-time)
- Insights chart: Top stent types by usage
- Refresh button to reload live data from CSV files

### Data Entry
- Add new stents to office stock
- Fields: Stent Type, Size, Batch No., Serial No., Entry Date, Expiry Date

### Stents Used
- Record stent usage against a patient
- Fields: Doctor, Hospital, Patient Name, Bill Amount, IPD No., Cath Lab No., Bill No., Stent Type, Size, Batch, Serial No., Entry Date, Expiry Date
- Moves stent from stock to used records

### Data Updation
- Update existing stent records in office stock or hospital stock

### Data Deletion
- Remove stent records from inventory

### FOC (Free of Charge)
- Mark stents as FOC — tracks stents provided at no cost

### Reports
Five built-in report tabs:
1. **Hospital List** — all hospitals registered in the system
2. **Hospital Report** — stent usage summary per hospital
3. **Doctor Stent Types** — which stent types each doctor uses
4. **Hospital Stent Types** — stent type breakdown per hospital
5. **All Stent Types** — complete stent type usage overview

### Invoice
- Generate billing invoices for stent usage
- Reads from invoice records and displays formatted billing data

---

## Tech Stack

| Library | Purpose |
|---|---|
| `tkinter` | Core GUI framework |
| `customtkinter` | Modern-styled widgets |
| `matplotlib` | Charts and analytics |
| `pandas` | Data processing |
| `numpy` | Numerical operations |
| `Pillow (PIL)` | Image handling |
| `tkcalendar` | Date picker widgets |
| `pickle` | Binary password storage |
| `csv` | CSV read/write |
| `datetime` | Date calculations |

---

## Project Structure

```
.
├── Project4.0.py        # Main application file (~3000 lines)
├── Dets.csv             # Hospital–Doctor–Stent Type mappings
├── officestock.csv      # Office stent inventory
├── hospitalstock.csv    # Hospital-level stent inventory
├── stentused.csv        # Used stent records (with patient/billing info)
├── Invoice.csv          # Invoice/billing records
├── Password.bin         # Encrypted credentials (auto-generated)
└── b.csv                # Auxiliary data file
```

---

## Data Files

### `Dets.csv`
Stores the mapping between hospitals, doctors, and stent types.

| Column | Description |
|---|---|
| Hospital | Hospital name |
| Doctor | Doctor name |
| Stent Type | Type of stent associated |

### `officestock.csv`
Tracks stents held in office inventory.

| Column | Description |
|---|---|
| Stent Type | Product name |
| Size | Diameter (mm) |
| Batch No. | Batch identifier |
| Serial No. | Unique serial number |
| Entry Date | Date added to stock |
| Expiry Date | Stent expiry date |

### `stentused.csv`
Records every stent that has been used in a procedure.

| Column | Description |
|---|---|
| Doctor | Performing doctor |
| Hospital | Hospital where used |
| Patient Name | Patient identifier |
| Bill Amount | Billing amount |
| IPD No. | In-patient department number |
| Cath Lab No. | Cath lab reference |
| Bill No. | Invoice/bill number |
| Stent Type | Type of stent |
| Size | Stent size |
| Batch No. | Batch number |
| Serial No. | Serial number |
| Entry Date | Procedure/entry date |
| Expiry Date | Stent expiry date |

---

## Supported Hospitals

- AIIMS Delhi
- Apollo Hospital
- Max Saket
- Medanta Medicity
- Fortis Gurgaon
- Kokilaben Dhirubhai Ambani Hospital
- Manipal Hospital
- Narayana Health
- Lilavati Hospital
- Sir Ganga Ram Hospital

---

## Supported Stent Types

- Orsiro Mission
- Promus Premier
- Resolute Onyx
- Xience Alpine
- Synergy Megatron
- MiStent SES
- BioMatrix Alpha
- Ultimaster Nagomi
- Supraflex Cruz
- Yukon Choice PC

---

## Installation

### Prerequisites
- Python 3.8+
- pip

### Install Dependencies

```bash
pip install customtkinter matplotlib pandas numpy Pillow tkcalendar
```

### Run the Application

```bash
python Project4.0.py
```

> **Note:** On first run, update the `base_path` variable in the script to point to your local data directory where CSV files are stored.

---

## Screenshots

> *Screenshots can be added here once the application is running.*

---

## How It Works

1. **Login** — Enter credentials to access the system. First-time users register via the New User option.
2. **Dashboard** — View real-time analytics loaded from CSV files.
3. **Add Stock** — Use Data Entry to add stents to office inventory.
4. **Record Usage** — Use Stents Used to log a procedure, moving a stent from stock to usage records.
5. **Generate Reports** — Use the Reports module for hospital and stent-wise summaries.
6. **Billing** — Use Invoice to generate and view billing records.

---

## License

This project was created as a semester academic submission. All rights reserved.
