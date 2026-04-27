from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import uuid
import os
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "hospital.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Models
class Appointment(BaseModel):
    name: str
    age: int
    gender: str
    phone: str
    email: Optional[str] = ""
    date: str
    time: str
    dept: str
    symptoms: str
    blood: Optional[str] = ""
    emergency: Optional[str] = ""

class AppointmentStatusUpdate(BaseModel):
    status: str

class Patient(BaseModel):
    name: str
    age: int
    gender: str
    phone: str
    blood: Optional[str] = ""
    emergency: Optional[str] = ""
    address: Optional[str] = ""
    history: Optional[str] = ""
    status: str = "active"
    dept: Optional[str] = ""

class Medication(BaseModel):
    patient_id: Optional[str] = None
    patient_name: str
    medicine: str
    dosage: str
    frequency: str
    start_date: str
    end_date: Optional[str] = ""
    prescribed_by: str
    dept: str
    notes: Optional[str] = ""

# API Endpoints

@app.post("/api/appointments")
def create_appointment(appt: Appointment):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    appt_id = str(uuid.uuid4())[:8]
    cursor.execute('''
        INSERT INTO appointments (id, name, age, gender, phone, email, date, time, dept, symptoms, blood, emergency, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (appt_id, appt.name, appt.age, appt.gender, appt.phone, appt.email, appt.date, appt.time, appt.dept, appt.symptoms, appt.blood, appt.emergency, 'pending'))
    conn.commit()
    conn.close()
    return {"id": appt_id, "status": "pending"}

@app.get("/api/admin/appointments")
def get_appointments():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM appointments ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.patch("/api/admin/appointments/{appt_id}")
def update_appointment_status(appt_id: str, status_update: AppointmentStatusUpdate):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE appointments SET status = ? WHERE id = ?', (status_update.status, appt_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/patients")
def get_patients():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM patients ORDER BY name ASC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/admin/patients")
def create_patient(patient: Patient):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    patient_id = str(uuid.uuid4())[:8]
    cursor.execute('''
        INSERT INTO patients (id, name, age, gender, phone, blood, emergency, address, history, status, dept)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (patient_id, patient.name, patient.age, patient.gender, patient.phone, patient.blood, patient.emergency, patient.address, patient.history, patient.status, patient.dept))
    conn.commit()
    conn.close()
    return {"id": patient_id}

@app.delete("/api/admin/patients/{patient_id}")
def delete_patient(patient_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM patients WHERE id = ?', (patient_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/admin/medications")
def get_medications():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM medications ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/admin/medications")
def create_medication(med: Medication):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    med_id = str(uuid.uuid4())[:8]
    cursor.execute('''
        INSERT INTO medications (id, patient_id, patient_name, medicine, dosage, frequency, start_date, end_date, prescribed_by, dept, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (med_id, med.patient_id, med.patient_name, med.medicine, med.dosage, med.frequency, med.start_date, med.end_date, med.prescribed_by, med.dept, med.notes))
    conn.commit()
    conn.close()
    return {"id": med_id}

@app.get("/api/stats")
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM appointments')
    total_appts = cursor.fetchone()[0]
    
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE date = ?', (today,))
    today_appts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'pending'")
    pending = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'confirmed'")
    confirmed = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM patients')
    total_patients = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM medications')
    total_meds = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_appointments": total_appts,
        "today_appointments": today_appts,
        "pending_confirmation": pending,
        "confirmed_today": confirmed,
        "total_patients": total_patients,
        "total_medications": total_meds
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
