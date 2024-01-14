import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import random
import re

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
            self.parking_system.parked_vehicles[vehicle_number] = {"entry_time": datetime.now(), "parking_slot": parking_slot}
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

        # Example: KA21XY7890

        pattern = re.compile(r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$')
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
            receipt += f"Total Cost: ₹{total_cost:.2f}"

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
                self.parked_vehicles_text.insert(tk.END, f"Vehicle {vehicle} parked at Slot {info['parking_slot']} since {info['entry_time']}\n")
        else:
            self.parked_vehicles_text.insert(tk.END, "No vehicles currently parked.")
        self.parked_vehicles_text.config(state=tk.DISABLED)

    def validate_input(self):
        vehicle_number = self.vehicle_number_entry.get().strip().upper()

        if not vehicle_number:
            messagebox.showwarning("Warning", "Please enter the vehicle number.")
            return False

        pattern = re.compile(r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$')
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
