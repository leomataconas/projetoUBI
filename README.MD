# Lab Access Control System

This project is a **Lab Access Control System** that uses RFID technology to manage and monitor access to a lab. The system consists of a Raspberry Pi, an RFID reader, a relay module, and an ESP32, all integrated with a Flask-based web application. The system allows authorized users to gain access to the lab by scanning their RFID cards, while administrators can manage users and monitor access logs through a web interface.

---

## Features

- **RFID-Based Access Control**: Users can gain access to the lab by scanning their RFID cards.
- **Real-Time Monitoring**: The web interface provides real-time updates on the lab's status and access logs.
- **User Management**: Admins can add or delete users through the web interface.
- **Secure Communication**: The system uses HTTPS and Basic Authentication to secure communication between clients and the server.
- **Scalable Architecture**: The system is designed to be scalable, with the potential for cloud integration and future enhancements.

---

## Hardware Components

- **Raspberry Pi**: Acts as the central server, running the Flask application and managing the database.
- **RFID Reader (MFRC522)**: Reads RFID tags and sends the data to the Raspberry Pi.
- **Relay Module**: Controls the door lock mechanism, unlocking the door for authorized users.
- **ESP32**: Acts as an alternative RFID reader, sending scanned RFID data to the Flask server over Wi-Fi.

---

## Connections

### RFID Reader to Raspberry Pi

| **RFID Pin** | **Raspberry Pi Pin** |
| ------------ | -------------------- |
| VCC          | 3.3V                 |
| RST          | GPIO 25              |
| GND          | GND                  |
| MISO         | GPIO 9               |
| MOSI         | GPIO 10              |
| SCK          | GPIO 11              |
| NSS          | GPIO 8               |

### Relay Module to Raspberry Pi

| **Relay Pin** | **Raspberry Pi Pin** |
| ------------- | -------------------- |
| S             | GPIO 18              |
| +             | 5V                   |
| -             | GND                  |

### RFID Reader to ESP32

| **RFID Pin** | **ESP32 Pin** |
| ------------ | ------------- |
| 3V3          | 3V3           |
| RST          | D22           |
| GND          | GND           |
| MISO         | D19           |
| MOSI         | D23           |
| SCK          | D18           |
| SDA          | D05           |

---

## Software Components

- **Flask**: A Python web framework used to build the lab attendance web application.
- **SQLite3**: A lightweight database used to store user data and access logs.
- **Nginx**: A high-performance web server used as a reverse proxy to route HTTP/HTTPS traffic to the Flask application.
- **Gunicorn**: A Python WSGI HTTP server used to serve the Flask application in production.
- **mDNS (Avahi)**: Used for automatic hostname resolution on the local network (`labattendance.local`).

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/lab-access-control-system.git
cd lab-access-control-system
```

### 2. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Configure Hardware

- Connect the RFID reader, relay module, and ESP32 to the Raspberry Pi as described in the **Connections** section.
- Ensure the Raspberry Pi is connected to the local network.

### 4. Configure Nginx and Gunicorn

- Set up Nginx as a reverse proxy for the Flask application. Refer to the `nginx.conf` file in the repository for the configuration.
- Configure Gunicorn to serve the Flask application. Use the following command to start Gunicorn:
  ```bash
  gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
  ```

### 5. Run the Flask Application

Start the Flask application:

```bash
python app.py
```

### 6. Access the Web Interface

- Open a web browser and navigate to `http://labattendance.local` (or the Raspberry Pi's IP address).
- Use the web interface to manage users and monitor access logs.

---

## Usage

### Adding a New User

1. Navigate to the **Add User** page.
2. Scan the user's RFID card.
3. Enter the user's name and click **Add User**.

### Deleting a User

1. Navigate to the **Delete User** page.
2. Scan the user's RFID card.
3. Click **Delete User**.

### Monitoring Access Logs

- The dashboard displays the current status of the lab, including the number of people present and a log of recent access events.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

