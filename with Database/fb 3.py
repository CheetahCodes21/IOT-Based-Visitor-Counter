import cv2
import pytesseract
import re
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import random
import pyrebase

from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()


# Set the path to the Tesseract OCR executable (change this according to your installation)
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

# Firebase configuration
config = {
    "apiKey": os.getenv("API_KEY"),
    "authDomain": "parkeasetesting-f25e5.firebaseapp.com",
    "databaseURL": "https://parkeasetesting-f25e5-default-rtdb.firebaseio.com",
    "storageBucket": "parkeasetesting-f25e5.appspot.com"
}



firebase = pyrebase.initialize_app(config)
db = firebase.database()

class ParkingSystem:
    def __init__(self, master):
        self.master = master
        self.master.title("Parking Billing System")

        # Create and configure widgets
        self.entry_button = tk.Button(master, text="Entry", command=self.entry_interface)
        self.exit_button = tk.Button(master, text="Exit", command=self.exit_interface)

        # Grid layout
        self.entry_button.grid(row=0, column=0, padx=10, pady=10)
        self.exit_button.grid(row=0, column=1, padx=10, pady=10)

        # Initialize the parking system
        self.load_data()  # Load existing data from the database

    def entry_interface(self):
        EntryInterface(self.master, self, self.update_exit_display)

    def exit_interface(self):
        ExitInterface(self.master, self)

    def update_exit_display(self):
        # Callback function to update the exit interface display
        if hasattr(self, 'exit_interface'):
            self.exit_interface.update_display()

    def load_data(self):
        try:
            data = db.child("parking_data").get().val()
            if data:
                self.parked_vehicles = data.get('parked_vehicles', {})
                self.available_parking_slots = set(data.get('available_parking_slots', range(1, 6)))
            else:
                # Initialize data if it doesn't exist
                self.parked_vehicles = {}
                self.available_parking_slots = set(range(1, 6))
        except Exception as e:
            print("Error loading data:", str(e))

    def save_data(self):
        data = {'parked_vehicles': self.parked_vehicles, 'available_parking_slots': list(self.available_parking_slots)}
        try:
            db.child("parking_data").set(data)
        except Exception as e:
            print("Error saving data:", str(e))

    def record_exit(self, vehicle_number, entry_time, exit_time, parking_slot, total_cost):
        exit_data = {
            "entry_time": entry_time.strftime("%Y-%m-%d %H:%M:%S"),
            "exit_time": exit_time.strftime("%Y-%m-%d %H:%M:%S"),
            "parking_slot": parking_slot,
            "total_cost": total_cost
        }

        try:
            db.child("parking_data").child("exit_logs").child(vehicle_number).set(exit_data)
        except Exception as e:
            print("Error recording exit data:", str(e))

class EntryInterface(tk.Toplevel):
    def __init__(self, master, parking_system, exit_callback):
        super().__init__(master)
        self.title("Parking Entry System")
        self.parking_system = parking_system
        self.exit_callback = exit_callback  # Callback function to update exit model

        # Call the license plate recognition code to obtain the result
        recognized_plate = detect_and_extract_number_plate()

        # Set the recognized license plate in the entry box after removing spaces
        recognized_plate = recognized_plate.replace(" ", "")
        self.vehicle_number_entry = tk.Entry(self)
        self.vehicle_number_entry.insert(tk.END, recognized_plate)

        # Grid layout
        self.vehicle_number_entry.grid(row=0, column=0, padx=10, pady=10)

        # Directly park the vehicle
        self.park_vehicle()

    def park_vehicle(self):
        if not self.validate_input():
            return

        vehicle_number = self.vehicle_number_entry.get()
        if vehicle_number in self.parking_system.parked_vehicles:
            messagebox.showwarning("Warning", f"Vehicle {vehicle_number} is already parked.")
        else:
            if not self.parking_system.available_parking_slots:
                messagebox.showwarning("Warning", "No available parking slots.")
                return

            # Assign a random parking slot
            parking_slot = random.choice(list(self.parking_system.available_parking_slots))
            entry_time = datetime.now()

            # Convert entry_time to string before storing in Firebase
            entry_time_str = entry_time.strftime("%Y-%m-%d %H:%M:%S")

            # Update Firebase database with entry information
            db.child("parking_data").child("entry_logs").child(vehicle_number).set({
                "entry_time": entry_time_str,
                "parking_slot": parking_slot
            })

            self.parking_system.parked_vehicles[vehicle_number] = {"entry_time": entry_time_str,
                                                                    "parking_slot": parking_slot}
            self.parking_system.available_parking_slots.remove(parking_slot)

            messagebox.showinfo("Success", f"Park {vehicle_number} at Slot {parking_slot}")
            self.destroy()  # Close the entry interface after parking

            # Update exit model
            if self.exit_callback:
                self.exit_callback()

            # Save data to the shared file
            self.parking_system.save_data()

    def validate_input(self, allow_empty=False):
        vehicle_number = self.vehicle_number_entry.get().strip().upper()

        if not allow_empty and not vehicle_number:
            messagebox.showwarning("Warning", "Please enter the vehicle number.")
            return False

        pattern = re.compile(r'^[A-Za-z]{2}\s?\d{2}\s?[A-Za-z]{1,2}\s?\d{4}$')
        if not pattern.match(vehicle_number):
            messagebox.showwarning("Warning", "Invalid vehicle number format.")
            return False

        return True

class ExitInterface(tk.Toplevel):
    def __init__(self, master, parking_system):
        super().__init__(master)
        self.title("Parking Exit System")
        self.parking_system = parking_system

        # Create and configure widgets
        self.vehicle_number_label = tk.Label(self, text="Vehicle Number:")
        self.vehicle_number_entry = tk.Entry(self)
        self.parked_vehicles_label = tk.Label(self, text="Parked Vehicles:")
        self.parked_vehicles_text = tk.Text(self, height=10, width=30, state=tk.DISABLED)

        # Call the license plate recognition code to obtain the result
        recognized_plate = detect_and_extract_number_plate()

        # Set the recognized license plate in the entry box after removing spaces
        recognized_plate = recognized_plate.replace(" ", "")
        self.vehicle_number_entry.insert(tk.END, recognized_plate)

        # Grid layout
        self.vehicle_number_label.grid(row=0, column=0, padx=10, pady=10)
        self.vehicle_number_entry.grid(row=0, column=1, padx=10, pady=10)
        self.parked_vehicles_label.grid(row=1, column=0, padx=10, pady=10, columnspan=3)
        self.parked_vehicles_text.grid(row=2, column=0, padx=10, pady=10, columnspan=3)

        # Directly print the receipt
        self.print_receipt()

    def print_receipt(self):
        if not self.validate_input():
            return

        vehicle_number = self.vehicle_number_entry.get()
        entry_info = db.child("parking_data").child("entry_logs").child(vehicle_number).get().val()

        if entry_info:
            entry_time = datetime.strptime(entry_info["entry_time"], "%Y-%m-%d %H:%M:%S")
            parking_slot = entry_info["parking_slot"]
            exit_time = datetime.now()
            duration = exit_time - entry_time
            total_hours = duration.total_seconds() / 3600
            parking_rate = 20  # Cost per hour
            total_cost = total_hours * parking_rate

            # Release the parking slot only when the vehicle exits
            self.parking_system.available_parking_slots.add(parking_slot)

            # Create receipt string
            receipt = f"Receipt for Vehicle {vehicle_number}\n"
            receipt += f"Parked at Slot {parking_slot} since {entry_time}\n"
            receipt += f"Exit Time: {exit_time}\n"
            receipt += f"Duration: {total_hours:.2f} hours\n"
            receipt += f"Total Cost: Rs.{total_cost:.2f}"

            # Print receipt
            print(receipt)

            # Record exit in Firebase
            self.parking_system.record_exit(vehicle_number, entry_time, exit_time, parking_slot, total_cost)

            # Show messagebox with billing information
            messagebox.showinfo("Billing Information", receipt)

            del self.parking_system.parked_vehicles[vehicle_number]
            self.vehicle_number_entry.delete(0, tk.END)  # Clear the entry field after exit
            self.update_display()

            # Save data to the shared file
            self.parking_system.save_data()
        else:
            messagebox.showwarning("Warning", f"Vehicle {vehicle_number} is not currently parked.")

    def update_display(self):
        self.parked_vehicles_text.config(state=tk.NORMAL)
        self.parked_vehicles_text.delete(1.0, tk.END)
        if self.parking_system.parked_vehicles:
            for vehicle, info in self.parking_system.parked_vehicles.items():
                self.parked_vehicles_text.insert(tk.END,
                                                 f"Vehicle {vehicle} parked at Slot {info['parking_slot']} since {info['entry_time']}\n")
        else:
            self.parked_vehicles_text.insert(tk.END, "No vehicles currently parked.")
        self.parked_vehicles_text.config(state=tk.DISABLED)

    def validate_input(self):
        vehicle_number = self.vehicle_number_entry.get().strip().upper()

        if not vehicle_number:
            messagebox.showwarning("Warning", "Please enter the vehicle number.")
            return False

        pattern = re.compile(r'^[A-Za-z]{2}\s?\d{2}\s?[A-Za-z]{1,2}\s?\d{4}$')
        if not pattern.match(vehicle_number):
            messagebox.showwarning("Warning", "Invalid vehicle number format.")
            return False

        return True

# Function to preprocess the image
def preprocess_image(image):
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter to reduce noise while preserving edges
    blurred = cv2.bilateralFilter(gray, 11, 17, 17)

    # Apply edge detection using the Canny detector
    edges = cv2.Canny(blurred, 30, 200)

    return edges

# Function to find contours in the processed image
def find_contours(image):
    # Find contours in the processed image
    contours, _ = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Filter out contours based on area
    filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 1000]

    # Sort contours by area in descending order
    filtered_contours = sorted(filtered_contours, key=cv2.contourArea, reverse=True)[:10]

    return filtered_contours

# Function to extract text from the image using Tesseract OCR
def extract_text_from_image(image):
    # Use Tesseract OCR to extract text from the image
    text = pytesseract.image_to_string(image, config='--oem 3 --psm 7')

    # Define a regex pattern for filtering
    pattern = re.compile(r'^[A-Za-z]{2}\s?\d{2}\s?[A-Za-z]{1,2}\s?\d{4}$')

    # Find the first match in the text
    match = pattern.search(text)

    # Extract the matched text or return an empty string if no match is found
    filtered_text = match.group() if match else ''

    # Remove spaces from the extracted text
    filtered_text = filtered_text.replace(" ", "")

    return filtered_text.strip()

# Function to save the image and extract filtered text
def save_and_extract_text(image):
    # Save the image
    cv2.imwrite('number_plate_image.jpg', image)

    # Read the saved image
    saved_image = cv2.imread('number_plate_image.jpg')

    # Extract filtered text from the saved image
    saved_image_text = extract_text_from_image(saved_image)
    print("Filtered Text from saved image:", saved_image_text)

    # Return the filtered text
    return saved_image_text

# Function to detect and extract the number plate
def detect_and_extract_number_plate():
    # Open the webcam
    cap = cv2.VideoCapture(0)

    # Flag to track whether a valid result has been found
    result_found = False

    while not result_found:
        # Capture a frame from the webcam
        ret, frame = cap.read()

        # Preprocess the frame
        processed_frame = preprocess_image(frame)

        # Find contours in the processed frame
        contours = find_contours(processed_frame)

        # Iterate through the contours and find the rectangle with the highest aspect ratio
        for contour in contours:
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Check if the contour is a rectangle
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)

                # Check if the aspect ratio is within a certain range (adjust as needed)
                aspect_ratio = float(w) / h
                if 2.0 < aspect_ratio < 6.0:
                    # Draw a rectangle around the number plate
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # Extract the region of interest (ROI) containing the number plate
                    roi = frame[y:y + h, x:x + w]

                    # Save the image and extract filtered text from the saved image
                    result = save_and_extract_text(roi)

                    # Check if a valid result is obtained
                    if result:
                        result_found = True
                        break

        # Display the original frame
        cv2.imshow("Webcam", frame)

        # Break the loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the webcam and close all windows
    cap.release()
    cv2.destroyAllWindows()

    # Return the result to the calling code
    return result

# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = ParkingSystem(root)
    root.mainloop()