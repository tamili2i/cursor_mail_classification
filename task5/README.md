# Doctor Appointment Booking API

A FastAPI-based REST API for managing doctor appointments.

## Features

- Doctor management (CRUD operations)
- Patient management (CRUD operations)
- Appointment scheduling and management
- Appointment status tracking
- Conflict checking for appointment slots
- Soft delete for doctors and patients

## Prerequisites

- Python 3.8+
- PostgreSQL database

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd task5
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following content:
```env
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=appointments
```

5. Create the database:
```bash
createdb appointments
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

2. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Doctors
- `GET /api/v1/doctors/` - List all doctors
- `POST /api/v1/doctors/` - Create a new doctor
- `GET /api/v1/doctors/{doctor_id}` - Get a specific doctor
- `PUT /api/v1/doctors/{doctor_id}` - Update a doctor
- `DELETE /api/v1/doctors/{doctor_id}` - Delete a doctor (soft delete)

### Patients
- `GET /api/v1/patients/` - List all patients
- `POST /api/v1/patients/` - Create a new patient
- `GET /api/v1/patients/{patient_id}` - Get a specific patient
- `PUT /api/v1/patients/{patient_id}` - Update a patient
- `DELETE /api/v1/patients/{patient_id}` - Delete a patient (soft delete)

### Appointments
- `GET /api/v1/appointments/` - List all appointments
- `POST /api/v1/appointments/` - Create a new appointment
- `GET /api/v1/appointments/{appointment_id}` - Get a specific appointment
- `PUT /api/v1/appointments/{appointment_id}` - Update an appointment
- `POST /api/v1/appointments/{appointment_id}/cancel` - Cancel an appointment

## Development

### Project Structure
```
task5/
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       ├── doctors.py
│   │       ├── patients.py
│   │       └── appointments.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── crud/
│   │   ├── doctor.py
│   │   ├── patient.py
│   │   └── appointment.py
│   ├── models/
│   │   ├── doctor.py
│   │   ├── patient.py
│   │   └── appointment.py
│   ├── schemas/
│   │   ├── doctor.py
│   │   ├── patient.py
│   │   └── appointment.py
│   └── main.py
├── requirements.txt
└── README.md
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Include docstrings (Google style)
- Use proper error handling

## License

This project is licensed under the MIT License. 