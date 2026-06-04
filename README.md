# 🚗 Smart Parking Slot Prediction System

An AI-powered Smart Parking Slot Prediction System that combines **IoT, Machine Learning, FastAPI, React, and Arduino** to provide real-time parking slot monitoring, automated slot allocation, and parking occupancy prediction.

---

## 📌 Overview

Finding an available parking space can be time-consuming and frustrating, especially in crowded areas. This project aims to solve this problem by providing a smart parking management solution that monitors parking slots in real time and predicts future availability using machine learning.

The system uses sensors to detect vehicle presence, processes the data through a backend server, and displays parking information on a user-friendly web dashboard.

---

## ✨ Features

* 🚘 Real-time parking slot monitoring
* 🤖 Machine Learning-based parking prediction
* 📊 Live parking occupancy dashboard
* 🔄 Automatic slot allocation and release
* 🌐 Responsive web interface
* 📡 IoT sensor integration with Arduino
* ⚡ FastAPI backend for high performance
* 🗄️ Database support for parking records
* 📈 Historical parking data analysis

---

## 🛠️ Tech Stack

### Frontend

* React.js
* TypeScript
* Tailwind CSS

### Backend

* FastAPI
* Python
* REST APIs

### Database

* PostgreSQL

### Machine Learning

* Scikit-learn
* Pandas
* NumPy

### Hardware

* Arduino UNO
* IR Sensors
* Servo Motor

---

## 🏗️ System Architecture

```text
Vehicle
   │
   ▼
IR Sensors
   │
   ▼
Arduino UNO
   │
   ▼
Serial Communication
   │
   ▼
FastAPI Backend
   │
 ┌─┴─────────┐
 ▼           ▼
Database   ML Model
   │
   ▼
React Dashboard
```

---

## 📂 Project Structure

```text
Parking-Slot-Prediction/
│
├── frontend/
│   ├── src/
│   ├── components/
│   └── pages/
│
├── backend/
│   ├── api/
│   ├── models/
│   ├── services/
│   └── database/
│
├── arduino/
│   └── parking_sensor_code/
│
├── machine_learning/
│   └── prediction_model/
│
└── README.md
```

---

## 🚀 Installation

### Clone the Repository

```bash
git clone https://github.com/your-username/Parking-Slot-Prediction.git
cd Parking-Slot-Prediction
```

### Backend Setup

```bash
cd backend

pip install -r requirements.txt

uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

---

## 📊 Machine Learning Module

The machine learning model analyzes historical parking data to:

* Predict parking slot availability
* Forecast occupancy trends
* Improve parking utilization
* Support intelligent parking decisions

### Algorithm Used

* Random Forest Regressor

---

## 🎯 Objectives

* Reduce time spent searching for parking spaces
* Improve parking space utilization
* Provide accurate parking availability predictions
* Enhance user convenience through automation
* Build a scalable smart parking solution

---

## 📸 Key Functionalities

✔ Real-Time Slot Detection

✔ Smart Parking Allocation

✔ Vehicle Entry & Exit Monitoring

✔ Occupancy Prediction

✔ Live Dashboard Updates

✔ Historical Data Analysis

✔ Automated Parking Management

---

## 🔮 Future Enhancements

* Mobile Application Support
* Cloud Deployment
* License Plate Recognition
* Online Parking Reservation
* Smart Payment Integration
* Multi-Parking Lot Management
* Deep Learning-Based Prediction Models

---

## 👨‍💻 Author

**Aaditya Prasad**

B.Tech Computer Science Engineering

Passionate about AI, Machine Learning, IoT, Cloud Computing, and Cybersecurity.

---

## 📜 License

This project is developed for educational and research purposes.
