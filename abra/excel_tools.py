import sqlite3
from pathlib import Path
from abra.database import get_db

try:
    from openpyxl import Workbook, load_workbook
    HAS_EXCEL = True
except:
    HAS_EXCEL = False

def import_clients_from_excel(excel_path):
    """Import clients from Excel. Columns: Name | Phone | ID_No | Location | Business | Guarantor | G_Phone"""
    if not HAS_EXCEL:
        return {"ok": False, "error": "openpyxl not installed"}
    wb = load_workbook(excel_path, data_only=True)
    ws = wb.active
    conn = get_db()
    cur = conn.cursor()
    imported = 0
    skipped = 0
    # Skip header row 1, start from row 2
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        name = str(row[0]).strip()
        phone = str(row[1] or "")
        id_no = str(row[2] or "")
        location = str(row[3] or "")
        business = str(row[4] or "")
        guarantor = str(row[5] or "")
        g_phone = str(row[6] or "")
        # Skip if already exists (same name + phone)
        exists = cur.execute("SELECT id FROM clients WHERE name=? AND phone=?", (name, phone)).fetchone()
        if exists:
            skipped += 1
            continue
        cur.execute("INSERT INTO clients (name,phone,id_no,location,business,guarantor,g_phone) VALUES (?,?,?,?,?,?,?)",
            (name, phone, id_no, location, business, guarantor, g_phone))
        imported += 1
    conn.commit()
    conn.close()
    return {"ok": True, "imported": imported, "skipped": skipped}

def export_clients_to_excel(save_path):
    """Export all clients + loans to Excel"""
    if not HAS_EXCEL:
        return {"ok": False, "error": "openpyxl not installed"}
    conn = get_db()
    cur = conn.cursor()
    wb = Workbook()
    # Sheet 1 - Clients
    ws1 = wb.active
    ws1.title = "Clients"
    ws1.append(["Name", "Phone", "ID_No", "Location", "Business", "Guarantor", "G_Phone", "Next_Kin", "Notes"])
    for r in cur.execute("SELECT name,phone,id_no,location,business,guarantor,g_phone,next_kin,notes FROM clients"):
        ws1.append(list(r))
    # Sheet 2 - Loans
    ws2 = wb.create_sheet("Loans")
    ws2.append(["Client", "Principal", "Interest", "Total", "Paid", "Balance", "Plan", "Date", "Due_Date", "Receipt"])
    for r in cur.execute("SELECT client_name,principal,interest,total,paid,balance,plan,date,due_date,receipt_no FROM loans"):
        ws2.append(list(r))
    # Sheet 3 - Cashbook
    ws3 = wb.create_sheet("Cashbook")
    ws3.append(["Time", "Type", "Client", "Method", "Amount", "By_Staff", "Note"])
    for r in cur.execute("SELECT time,type,client,method,amount,by_staff,note FROM cashbook"):
        ws3.append(list(r))
    wb.save(save_path)
    conn.close()
    return {"ok": True, "path": str(save_path)}

def export_template_to_excel(save_path):
    """Create empty template for SACCO to fill"""
    if not HAS_EXCEL:
        return {"ok": False, "error": "openpyxl not installed"}
    wb = Workbook()
    ws = wb.active
    ws.title = "Clients"
    ws.append(["Name", "Phone", "ID_No", "Location", "Business", "Guarantor", "G_Phone"])
    ws.append(["John Mukasa", "0770123456", "CM123456", "Kampala", "Boda", "Peter Ssemwanga", "0700123456"])
    wb.save(save_path)
    return {"ok": True, "path": str(save_path)}
