 **Comprehensive explanation of finalcode.py program:**

**Import Statements:**

- **import cv2:** Imports the OpenCV library for image and video processing tasks.
- **import pytesseract:** Imports the Tesseract OCR library for extracting text from images.
- **import re:** Imports the regular expressions library for pattern matching and text filtering.
- **import tkinter as tk:** Imports the Tkinter library for creating graphical user interfaces.
- **from tkinter import messagebox:** Imports the messagebox module for displaying pop-up messages.
- **from datetime import datetime, timedelta:** Imports the datetime module for working with dates and times.
- **import random:** Imports the random module for generating random numbers.

**License Plate Recognition Functions:**

- **preprocess_image(image):** Prepares an image for text extraction:
    - Converts the image to grayscale using `cv2.cvtColor`.
    - Reduces noise while preserving edges using `cv2.bilateralFilter`.
    - Applies edge detection using `cv2.Canny` to highlight text regions.
    - Returns the processed image with enhanced edges.
- **find_contours(image):** Finds potential text regions in the image:
    - Detects contours (continuous outlines of shapes) using `cv2.findContours`.
    - Filters contours based on their area to remove small or insignificant ones.
    - Sorts the remaining contours by area in descending order, assuming larger contours are more likely to contain text.
    - Returns a list of the filtered and sorted contours.
- **extract_text_from_image(image):** Extracts text using Tesseract OCR:
    - Uses `pytesseract.image_to_string` to extract text from the image.
    - Applies filtering using regular expressions to refine the results and match specific patterns like license plate formats.
    - Returns the filtered text.
- **save_and_extract_text(image):** Saves the image and extracts text from it:
    - Saves the image using `cv2.imwrite`.
    - Reloads the saved image using `cv2.imread`.
    - Calls `extract_text_from_image` to extract text from the saved image.
    - Prints the extracted text.
    - Returns the extracted text.
- **detect_and_extract_number_plate():** Captures frames from a webcam and extracts the number plate:
    - Opens the webcam using `cv2.VideoCapture(0)`.
    - Loops continuously:
        - Captures a frame from the webcam using `cap.read`.
        - Preprocesses the frame using `preprocess_image`.
        - Finds contours in the preprocessed frame using `find_contours`.
        - Iterates through contours to identify rectangles with suitable aspect ratios (potential number plates).
        - Extracts regions of interest (ROIs) containing potential number plates.
        - Extracts text from the ROIs using `save_and_extract_text`.
        - If a valid result (number plate text) is found, breaks the loop.
    - Releases the webcam using `cap.release`.
    - Returns the extracted number plate text.

**Parking System Classes:**

- **EntryInterface:** Handles vehicle entry:
    - Inherits from Tkinter's Toplevel class to create a separate window.
    - Creates widgets for vehicle number entry and parking button.
    - Uses `detect_and_extract_number_plate` to capture the license plate and display it in the entry box.
    - Handles parking vehicle logic:
        - Validates input (checks for empty or invalid vehicle numbers).
        - Checks for available parking slots.
        - Assigns a random parking slot if available.
        - Updates parking records (vehicle number, entry time, parking slot) in the `ParkingSystem` object.
        - Displays success message.
        - Updates the exit interface (if applicable) to reflect parking information.
- **ExitInterface:** Handles vehicle exit and payment:
    - Similar structure to EntryInterface, with widgets for vehicle number entry and payment button.
    - Handles exiting vehicle logic:
        - Validates input (checks for empty or invalid vehicle numbers).
        - Retrieves parking information for the entered vehicle number.
        - Calculates parking duration and cost based on entry time and current time.
        - Generates a receipt string with billing information.
        - Displays the receipt using `messagebox.showinfo`.
        - Updates parking records (removes vehicle, releases parking slot)