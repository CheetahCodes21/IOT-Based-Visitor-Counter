import cv2
import pytesseract
import re
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import random

# Set the path to the Tesseract OCR executable (change this according to your installation)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Set the path to the Tesseract OCR executable (change this according to your installation)
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'


def preprocess_image(image):
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter to reduce noise while preserving edges
    blurred = cv2.bilateralFilter(gray, 11, 17, 17)

    # Apply edge detection using the Canny detector
    edges = cv2.Canny(blurred, 30, 200)

    return edges


def find_contours(image):
    # Find contours in the processed image
    contours, _ = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Filter out contours based on area
    filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 1000]

    # Sort contours by area in descending order
    filtered_contours = sorted(filtered_contours, key=cv2.contourArea, reverse=True)[:10]

    return filtered_contours


def extract_text_from_image(image):
    # Use Tesseract OCR to extract text from the image
    text = pytesseract.image_to_string(image, config='--oem 3 --psm 7')

    # Define a regex pattern for filtering
    pattern = re.compile(r'^[A-Za-z]{2}\s?\d{2}\s?[A-Za-z]{1,2}\s?\d{4}$')

    # Find the first match in the text
    match = pattern.search(text)

    # Extract the matched text or return an empty string if no match is found
    filtered_text = match.group() if match else ''

    return filtered_text.strip()


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


class EntryInterface(tk.Toplevel):
    def __init__(self, master, parking_system, exit_callback):
        super().__init__(master)
        self.title("Parking Entry System")
        self.parking_system = parking_system
        self.exit_callback = exit_callback  # Callback function to update exit model

        # Create and configure widgets
        self.vehicle_number_label = tk.Label(self, text="Vehicle Number:")
        self.vehicle_number_entry = tk.Entry(self)
        self.park_button = tk.Button(self, text="Park Vehicle", command=self.park_vehicle)

        # Call the license plate recognition code to obtain the result
        recognized_plate = detect_and_extract_number_plate()

        # Set the recognized license plate in the entry box
        self.vehicle_number_entry.insert(tk.END, recognized_plate)

        # Grid layout
        self.vehicle_number_label.grid(row=0, column=0, padx=10, pady=10)
        self.vehicle_number_entry.grid(row=0, column=1, padx=10, pady=10)
        self.park_button.grid(row=0, column=2, padx=10, pady=10)

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
            self.parking_system.parked_vehicles[vehicle_number] = {"entry_time": datetime.now(),
                                                                    "parking_slot": parking_slot}
            self.parking_system.available_parking_slots.remove(parking_slot)

            messagebox.showinfo("Success", f"Vehicle {vehicle_number} parked at Slot {parking_slot}")
            self.destroy()  # Close the entry interface after parking

            # Update exit model
            if self.exit_callback:
                self.exit_callback()

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
        self.pay_and_exit_button = tk.Button(self, text="Pay and Exit", command=self.pay_and_exit)
        self.parked_vehicles_label = tk.Label(self, text="Parked Vehicles:")
        self.parked_vehicles_text = tk.Text(self, height=10, width=30, state=tk.DISABLED)

        # Call the license plate recognition code to obtain the result
        recognized_plate = detect_and_extract_number_plate()

        # Set the recognized license plate in the entry box
        self.vehicle_number_entry.insert(tk.END, recognized_plate)

        # Grid layout
        self.vehicle_number_label.grid(row=0, column=0, padx=10, pady=10)
        self.vehicle_number_entry.grid(row=0, column=1, padx=10, pady=10)
        self.pay_and_exit_button.grid(row=0, column=2, padx=10, pady=10)
        self.parked_vehicles_label.grid(row=1, column=0, padx=10, pady=10, columnspan=3)
        self.parked_vehicles_text.grid(row=2, column=0, padx=10, pady=10, columnspan=3)

        # Update the display initially
        self.update_display()

    def pay_and_exit(self):
        if not self.validate_input():
            return

        vehicle_number = self.vehicle_number_entry.get()
        if vehicle_number in self.parking_system.parked_vehicles:
            entry_time = self.parking_system.parked_vehicles[vehicle_number]["entry_time"]
            parking_slot = self.parking_system.parked_vehicles[vehicle_number]["parking_slot"]
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
            receipt += f"Duration: {total_hours:.2f} hours\n"
            receipt += f"Total Cost: ${total_cost:.2f}"

            # Print receipt
            print(receipt)

            # Show messagebox with billing information
            messagebox.showinfo("Billing Information", receipt)

            del self.parking_system.parked_vehicles[vehicle_number]
            self.vehicle_number_entry.delete(0, tk.END)  # Clear the entry field after exit
            self.update_display()
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
        self.parked_vehicles = {}  # Dictionary to store vehicle numbers and entry times
        self.available_parking_slots = set(range(1, 6))  # Assuming 5 parking slots

    def entry_interface(self):
        EntryInterface(self.master, self, self.update_exit_display)

    def exit_interface(self):
        ExitInterface(self.master, self)

    def update_exit_display(self):
        # Callback function to update the exit interface display
        if hasattr(self, 'exit_interface'):
            self.exit_interface.update_display()


if __name__ == "__main__":
    root = tk.Tk()
    app = ParkingSystem(root)
    root.mainloop()
