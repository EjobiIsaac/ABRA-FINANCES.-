import sys
import json
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFileDialog
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QObject, Slot
from PySide6.QtWebChannel import QWebChannel

from abra.database import init_db, get_db
from abra.license_manager import check_license, activate_key, _make_key, _machine_id
from abra.config import BASE_DIR
from abra.excel_tools import import_clients_from_excel, export_clients_to_excel, export_template_to_excel

if getattr(sys, 'frozen', False):
    HTML_FILE = Path(sys._MEIPASS) / "abra_ui.html"
else:
    HTML_FILE = Path(__file__).parent / "abra_ui.html"

class Bridge(QObject):
    @Slot(str, result=str)
    def call(self, payload):
        try:
            data = json.loads(payload)
            action = data.get("action")
            conn = get_db()
            cur = conn.cursor()

            if action == "save_client":
                c = data["client"]
                cur.execute("INSERT INTO clients (name,phone,id_no,location,business,guarantor,g_phone,guarantor2,next_kin,notes,photo) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (c.get("name"), c.get("phone"), c.get("idNo"), c.get("location"), c.get("business"), c.get("guarantor"), c.get("gPhone"), c.get("guarantor2"), c.get("nextKin"), c.get("notes"), c.get("photo","")))
                conn.commit()
                return json.dumps({"ok": True, "id": cur.lastrowid})

            if action == "get_clients":
                rows = cur.execute("SELECT * FROM clients ORDER BY id DESC").fetchall()
                return json.dumps({"ok": True, "clients": [dict(r) for r in rows]})

            if action == "save_loan":
                l = data["loan"]
                cur.execute("INSERT INTO loans (client_id,client_name,principal,interest,total,paid,balance,plan,duration,penalty,collateral,date,due_date,receipt_no) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (l.get("clientId"), l.get("clientName"), l.get("principal"), l.get("interest"), l.get("total"), l.get("paid",0), l.get("balance"), l.get("plan"), l.get("duration"), l.get("penalty"), l.get("collateral"), l.get("date"), l.get("dueDate"), l.get("receiptNo")))
                conn.commit()
                return json.dumps({"ok": True})

            if action == "get_loans":
                rows = cur.execute("SELECT * FROM loans ORDER BY id DESC").fetchall()
                return json.dumps({"ok": True, "loans": [dict(r) for r in rows]})

            if action == "add_payment":
                p = data["payment"]
                cur.execute("UPDATE loans SET paid = paid + ?, balance = balance - ? WHERE id = ?", (p["amount"], p["amount"], p["loanId"]))
                cur.execute("INSERT INTO cashbook (time,type,client,method,amount,by_staff,note,loan_id) VALUES (?,?,?,?,?,?,?,?)",
                    (p.get("time"), "Repayment", p.get("client"), p.get("method"), p.get("amount"), p.get("byStaff"), p.get("note"), p.get("loanId")))
                conn.commit()
                return json.dumps({"ok": True})

            if action == "get_cashbook":
                rows = cur.execute("SELECT * FROM cashbook ORDER BY id DESC").fetchall()
                return json.dumps({"ok": True, "cashbook": [dict(r) for r in rows]})

            if action == "get_settings":
                row = cur.execute("SELECT value FROM settings WHERE key='biz'").fetchone()
                return json.dumps({"ok": True, "settings": json.loads(row["value"]) if row else {}})

            if action == "save_settings":
                cur.execute("UPDATE settings SET value=? WHERE key='biz'", (json.dumps(data["settings"]),))
                conn.commit()
                return json.dumps({"ok": True})

            if action == "import_excel":
                conn.close()
                return json.dumps(import_clients_from_excel(data.get("path")))

            if action == "export_excel":
                conn.close()
                return json.dumps(export_clients_to_excel(data.get("path")))

            if action == "export_template":
                conn.close()
                return json.dumps(export_template_to_excel(data.get("path")))

            conn.close()
            return json.dumps({"ok": False, "error": "unknown action"})
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e)})

class LicenseDialog(QDialog):
    def __init__(self, lic):
        super().__init__()
        self.setWindowTitle("ABRA FINANCES - License")
        self.setFixedSize(420, 260)
        layout = QVBoxLayout()
        if lic["status"] == "trial":
            layout.addWidget(QLabel(f"ABRA FINANCES - Trial\n\nYou have {lic['days_left']} days left.\n\nMachine ID: {lic['machine_id']}\n\nSend this Machine ID to SAVVY SOFT to buy a key."))
        else:
            layout.addWidget(QLabel(f"TRIAL EXPIRED\n\nMachine ID: {lic['machine_id']}\n\nEnter your license key to continue:"))
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("ABRA-XXXX-365-XXXX")
        layout.addWidget(self.key_input)
        btn = QPushButton("Activate" if lic["status"] == "expired" else "Activate Key / Continue Trial")
        btn.clicked.connect(self.try_activate)
        layout.addWidget(btn)
        self.setLayout(layout)
        self.lic = lic
    def try_activate(self):
        key = self.key_input.text().strip()
        if not key:
            if self.lic["status"] == "trial":
                self.accept()
                return
            QMessageBox.warning(self, "Locked", "Please enter a license key.")
            return
        if activate_key(key):
            QMessageBox.information(self, "Success", "ABRA Activated! Thank you.")
            self.accept()
        else:
            QMessageBox.warning(self, "Wrong Key", "This key does not match this PC. Check Machine ID.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ABRA FINANCES")
        self.resize(1280, 800)
        self.view = QWebEngineView()
        self.channel = QWebChannel()
        self.bridge = Bridge()
        self.channel.registerObject("abra", self.bridge)
        self.view.page().setWebChannel(self.channel)
        self.view.load(QUrl.fromLocalFile(str(HTML_FILE)))
        self.setCentralWidget(self.view)

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    lic = check_license()
    if lic["status"] == "expired":
        dlg = LicenseDialog(lic)
        if dlg.exec() != QDialog.Accepted:
            sys.exit(0)
    elif lic["status"] == "trial":
        dlg = LicenseDialog(lic)
        dlg.exec()
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
