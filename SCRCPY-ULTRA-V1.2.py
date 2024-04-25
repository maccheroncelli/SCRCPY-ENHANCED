# SWANTEK INDUSTRIES 2024

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, QTextEdit, QFileDialog, QGroupBox, QDesktopWidget
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QTextOption
import sys
import subprocess
import os
import threading
import pyautogui
import imagehash
import cv2
import datetime
import time
import numpy as np
import io
import math
import PyPDF2
import xml.etree.ElementTree as ET
from io import BytesIO
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader

# Make sure to replace 'adb_path' with the path to your adb executable if it's not in your PATH environment variable
adb_path = 'adb'

Image.MAX_IMAGE_PIXELS = None  # This removes the threshold limit to avoid DecompressionBombError
CUSTOM_EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

# Constants for PDF page limits
MAX_PDF_PAGE_HEIGHT = 14400
MAX_PDF_PAGE_WIDTH = 14400

class CustomEvent(QEvent):
    def __init__(self, callback):
        super().__init__(CUSTOM_EVENT_TYPE)
        self.callback = callback

class SCRCPYULTRA(QWidget):

    # Define a custom signal
    processEnded = pyqtSignal()
    
    # Define a custom signal for logging messages
    logMessageSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.scrcpy_process = None
        self.logMessageSignal.connect(self.logMessage)
        self.processEnded.connect(self.enableUIElements)
        self.autoscroll_screenshot_paths = []  # Initialize the list to track screenshots
        self.lastAction = None  # To track the last action (autoscroll or manual stitch)
        # Get the directory of the script or the current working directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Define the output folder path
        self.output_folder = os.path.join(script_dir, 'AndroidScreenOutput')
        # Create the output folder if it does not exist
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('SCRCPY ULTRA')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)  # Keep window on top
        mainLayout = QVBoxLayout(self)
        
        # Get available geometry from the screen the widget is on
        screen_rect = self.screen().availableGeometry()

        # Calculate the coordinates
        x = screen_rect.width() - self.width() - int(screen_rect.width() * 0.05)  # 5% from the right edge of the screen
        y = int(screen_rect.height() * 0.05)  # 5% from the top of the screen

        # Set the window to the new position
        self.move(x, y)

        # SCRCPY Functionality GroupBox
        scrcpyGroupBox = QGroupBox("")
        scrcpyLayout = QVBoxLayout(scrcpyGroupBox)
        scrcpyLayout.addWidget(QLabel('SCRCPY Functionality:'))
        self.functionalityCombo = QComboBox()
        self.functionalityCombo.addItems(['Screenshots', 'Screen recording'])
        scrcpyLayout.addWidget(self.functionalityCombo)
        self.startBtn = QPushButton('Start SCRCPY')
        self.startBtn.clicked.connect(self.startSCRCPY)  # Make sure to connect your signals to slots
        scrcpyLayout.addWidget(self.startBtn)
        mainLayout.addWidget(scrcpyGroupBox)

        # Autoscroll & OCR Settings GroupBox
        autoscrollGroupBox = QGroupBox("")
        autoscrollLayout = QVBoxLayout(autoscrollGroupBox)
        self.addOCRSettings(autoscrollLayout)
        self.addAutoscrollSettings(autoscrollLayout)
        mainLayout.addWidget(autoscrollGroupBox)

        # Cropping and Stitching GroupBox
        cropStitchGroupBox = QGroupBox("")
        cropStitchLayout = QVBoxLayout(cropStitchGroupBox)
        self.addCropStitchSettings(cropStitchLayout)
        mainLayout.addWidget(cropStitchGroupBox)

        # Information GroupBox
        infoGroupBox = QGroupBox("Information")
        infoLayout = QVBoxLayout(infoGroupBox)
        self.addInformationSettings(infoLayout)
        mainLayout.addWidget(infoGroupBox)

        self.setLayout(mainLayout)
        self.resize(400, 500)
        
    def centerRight(self):
        qr = self.frameGeometry()
        screen = QDesktopWidget().availableGeometry()
        centerPoint = screen.center()
        
        # Explicit calculation for centering
        newX = centerPoint.x() - qr.width() // 2
        newY = centerPoint.y() - qr.height() // 2
        
        self.move(newX, newY)

    def addOCRSettings(self, layout):
        layout.addWidget(QLabel('Optical Character Recognition (OCR):'))
        self.ocrCombo = QComboBox()
        self.ocrCombo.addItems(['OCR Disabled', 'OCR Enabled (Tesseract)']) # , 'Screen Dump (UiAutomate)'     Insert combo option to enable UiAutomate Dumps (Experimental!)
        layout.addWidget(self.ocrCombo)
        screenshotBtn = QPushButton('Screenshot')
        screenshotBtn.clicked.connect(self.takeScreenshot)  
        layout.addWidget(screenshotBtn)

    def addAutoscrollSettings(self, layout):
        layout.addWidget(QLabel('Swipe Direction:'))
        self.scrollCombo = QComboBox()
        self.scrollCombo.addItems(['UP', 'DOWN'])
        layout.addWidget(self.scrollCombo)
        
        # Swipe Speed
        layout.addWidget(QLabel("Swipe Speed:"))
        self.swipeSpeedComboBox = QComboBox()
        for i in range(1, 500):  # Fill with numbers from 1 to 499
            self.swipeSpeedComboBox.addItem(str(i))
        self.swipeSpeedComboBox.setCurrentIndex(124)  # Set default value
        layout.addWidget(self.swipeSpeedComboBox)

        # Swipe Count
        layout.addWidget(QLabel("Swipe Count:"))
        self.scrollCountComboBox = QComboBox()
        self.scrollCountComboBox.addItem("Infinite")  # Add "Infinite" instead of "0"
        for i in range(2, 101):  # Fill with numbers from 1 to 100
            self.scrollCountComboBox.addItem(str(i))
        layout.addWidget(self.scrollCountComboBox)

        # Swipe Delay
        layout.addWidget(QLabel("Swipe Delay (Seconds):"))
        self.scrollDelayComboBox = QComboBox()
        for i in range(21):  # 21 because 0 to 2 (inclusive) with steps of 0.1 gives us 21 values
            value = i * 0.1  # Calculate the current value
            self.scrollDelayComboBox.addItem(f"{value:.1f}")
        self.scrollDelayComboBox.setCurrentIndex(10)  # Set default value
        layout.addWidget(self.scrollDelayComboBox)
        
        # Post Processing
        self.postCombo = QComboBox()
        self.postCombo.addItems(['None', 'Crop', 'Crop + Stitch'])
        layout.addWidget(QLabel('Post Processing:'))
        layout.addWidget(self.postCombo)

        self.startScrollBtn = QPushButton('Start Autoscroll')
        self.startScrollBtn.clicked.connect(self.startAutoScrollScreenshots) 
        layout.addWidget(self.startScrollBtn)
        
        self.testSwipeBtn = QPushButton('Test Swipe Speed')
        self.testSwipeBtn.clicked.connect(self.swipeScreen) 
        layout.addWidget(self.testSwipeBtn)

    def addCropStitchSettings(self, layout):
        ocrBtn = QPushButton('Manual OCR')
        ocrBtn.clicked.connect(self.manualOCR)  
        layout.addWidget(ocrBtn)
        cropBtn = QPushButton('Manual Crop')
        cropBtn.clicked.connect(self.bulkImageCrop)  
        layout.addWidget(cropBtn)
        layout.addWidget(QLabel('Stitch Direction'))
        self.directionCombo = QComboBox()
        self.directionCombo.addItems(['UP', 'DOWN'])
        layout.addWidget(self.directionCombo)
        stitchBtn = QPushButton(' Manual Stitch')
        stitchBtn.clicked.connect(self.onStitchButtonClick)  
        layout.addWidget(stitchBtn)

    def addInformationSettings(self, layout):
        self.logArea = QTextEdit()
        self.logArea.setReadOnly(True)
        self.logArea.setWordWrapMode(QTextOption.NoWrap)  # Ensure no word wrap
        layout.addWidget(self.logArea)
        helpBtn = QPushButton('README')
        helpBtn.clicked.connect(self.displayHelp)
        layout.addWidget(helpBtn)

    def logMessage(self, message):
        """Logs a message to the QTextEdit log area with a timestamp."""
        timestamp = datetime.datetime.now().strftime("%y/%m/%d %H:%M | ")
        self.logArea.append(timestamp + message)
        
    def event(self, event):
            # Check if the event is a CustomEvent and handle it
            if event.type() == CUSTOM_EVENT_TYPE:
                event.callback()
                return True
            return super().event(event)

    def displayHelp(self):
        readme_path = 'README.txt'
        try:
            if sys.platform == "win32":
                os.startfile(readme_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", readme_path])
            else:  # Assuming Linux or similar
                subprocess.run(["xdg-open", readme_path])
        except Exception as e:
            self.logMessageSignal.emit(f"Error opening README file: {str(e)}")

    def startSCRCPY(self):
        functionality = self.functionalityCombo.currentText()
        
        # Disable the start button and functionality combo box
        self.startBtn.setDisabled(True)
        self.functionalityCombo.setDisabled(True)

        try:
            # For standard SCRCPY functionality
            if 'Screen recording' in functionality or 'Screenshots' in functionality:
                # Start the SCRCPY process based on selected functionality
                if functionality == 'Screen recording':
                    self.scrcpy_process = subprocess.Popen(['scrcpy', '--record', os.path.join(self.output_folder, f'{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp4')])
                    self.logMessageSignal.emit("SCRCPY process has started successfully")
                elif functionality == 'Screenshots':
                    self.scrcpy_process = subprocess.Popen(['scrcpy'])
                    self.logMessageSignal.emit("SCRCPY process has started successfully")
                else:
                    raise Exception("SCRCPY failed to start.")

                # Start a thread to monitor the SCRCPY process
                monitor_thread = threading.Thread(target=self.monitorSCRCPYProcess)
                monitor_thread.daemon = True
                monitor_thread.start()
        except Exception as e:
            self.logMessageSignal.emit(f"Failed to start SCRCPY: {str(e)}")
            # Re-enable the UI elements if SCRCPY fails to start immediately
            self.enableUIElements()
            
    def monitorSCRCPYProcess(self):
        if self.scrcpy_process:
            self.scrcpy_process.wait()  # Wait for the SCRCPY process to exit
            self.scrcpy_process = None
            self.logMessageSignal.emit("SCRCPY process has ended.")
            # Re-enable UI elements in the main thread
            self.enableUIElementsOnUIThread()

    def enableUIElementsOnUIThread(self):
        # Check if this method is called from a non-UI thread
        if not self.startBtn.isEnabled():
            # Use QCoreApplication.postEvent or similar mechanism to run enableUIElements on the main thread
            QApplication.postEvent(self, CustomEvent(self.enableUIElements))

    def enableUIElements(self):
        self.functionalityCombo.setEnabled(True)
        self.ocrCombo.setEnabled(True)
        self.startBtn.setEnabled(True)

    def takeScreenshot(self):
        # Create a timestamp for naming the screenshot file
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        try:
            # Execute adb command to take a screenshot from the connected Android device
            screenshot_data = subprocess.check_output([adb_path, 'exec-out', 'screencap', '-p'])
        except subprocess.CalledProcessError as e:
            # If adb command fails, log the error and return None
            self.logMessageSignal.emit(f"Error taking screenshot: No device connected...")
            return None
        
        # Convert raw screenshot data into an image stream
        image_stream = BytesIO(screenshot_data)
        
        # Open the image from the stream
        image = Image.open(image_stream)
        
        # Create a filename for the screenshot with the current timestamp
        output_filename = f'{timestamp}.png'
        
        # Build the full path where the screenshot will be saved
        screenshot_path = os.path.join(self.output_folder, output_filename)
        
        # Save the screenshot to the output path
        image.save(screenshot_path)
        
        # Append the path of the taken screenshot to the list for tracking
        self.autoscroll_screenshot_paths.append(screenshot_path)
        
        # Log the successful capture and saving of the screenshot
        self.logMessageSignal.emit(f"Screenshot taken and saved as: {output_filename}")
        
        # Check if OCR (Optical Character Recognition) is enabled via the GUI or if Screen Dump is selected
        ocr_option = self.ocrCombo.currentText()
        if ocr_option != 'OCR Disabled':
            if ocr_option.startswith('OCR Enabled'):
                # If OCR is enabled, call the performOCR function with the path of the new screenshot
                self.performOCR(screenshot_path)
            elif ocr_option == 'Screen Dump (UiAutomate)':
                # Handle UI Automate dump
                ui_dump_path = screenshot_path.replace('.png', '_screendump.xml')
                text_output_path = screenshot_path.replace('.png', '_screendump.txt')
                self.dump_ui_xml_and_save(ui_dump_path)
                self.extract_generic_text_from_ui_dump(ui_dump_path, text_output_path)
        
        # Return the Image object, might be useful for other operations
        return image
        
    def manualOCR(self):
        # Open file dialog to let the user select images for OCR
        fileNames, _ = QFileDialog.getOpenFileNames(self, "Select Images for OCR", self.output_folder, "Images (*.png *.jpg *.jpeg)")
        if not fileNames:
            self.logMessageSignal.emit("No images selected for OCR.")
            return

        # Loop through each selected file and perform OCR
        for fileName in fileNames:
            self.performOCR(fileName, manual=True)
            
    def performOCR(self, screenshot_path, manual=False):
        """
        Perform OCR on the provided screenshot path. If the image is too large, it will be segmented.
        Each segment is converted to a high-contrast PDF if required and then OCR is performed.
        The OCR results are combined into a final PDF.
        """
        timestamp = os.path.basename(screenshot_path).replace('.png', '')
        self.logMessageSignal.emit("OCR enabled, processing screenshot...")
        
        img = Image.open(screenshot_path)
        segments = []
        
        # If the image is too large, split into segments
        if img.height > MAX_PDF_PAGE_HEIGHT or img.width > MAX_PDF_PAGE_WIDTH:
            self.logMessageSignal.emit("Image too large, splitting into segments for OCR...")
            segments = self.split_image(img, timestamp)
        else:
            segments = [screenshot_path]

        # Process each segment with OCR
        ocr_segments = [self.process_single_segment(segment, timestamp, manual) for segment in segments]
        
        # Combine the OCR results if there were multiple segments
        if len(ocr_segments) > 1:
            combined_pdf_path = self.combine_ocr_segments(ocr_segments, timestamp)     
            if combined_pdf_path:
                # Perform cleanup here after successful combination
                self.clean_up_segments(segments, ocr_segments)
        else:
            combined_pdf_path = ocr_segments[0] if ocr_segments else None
        
        # Final log message for completion
        if combined_pdf_path:
            self.logMessageSignal.emit(f"OCR process completed for image: {screenshot_path}")
            return combined_pdf_path
        else:
            self.logMessageSignal.emit("OCR process failed or was skipped due to image segmentation.")
            return None

    def process_single_segment(self, segment_path, timestamp, manual):
        """
        Convert a single image segment to a high-contrast PDF, perform OCR on it, and return the path to the OCR'd PDF.
        """
        segment_pdf_path = segment_path.replace('.png', '.pdf')
        high_contrast = 'Tesseract' in self.ocrCombo.currentText()

        # Convert image to high-contrast PDF if required
        if high_contrast or manual:
            # Apply high contrast conversion and save as PDF
            self.convert_to_high_contrast_and_save_as_pdf(segment_path, segment_pdf_path)
        else:
            self.convert_image_to_pdf(segment_path, segment_pdf_path)

        # Perform OCR on the segment
        ocr_segment_path = segment_pdf_path.replace('.pdf', '_OCR.pdf')
        self.ocrmypdf(segment_pdf_path, ocr_segment_path, True)
        return ocr_segment_path

    def convert_to_high_contrast_and_save_as_pdf(self, image_path, pdf_path):
        """
        Convert the image at the given path to a high-contrast version and save it as a PDF.
        """
        img = Image.open(image_path).convert('L')  # Convert to grayscale for high contrast
        pdf_bytes = io.BytesIO()
        img.save(pdf_bytes, format='PDF')
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes.getvalue())
        self.logMessageSignal.emit(f"High contrast PDF created for OCR: {pdf_path}")

    def combine_ocr_segments(self, ocr_segments, timestamp):
        """
        Combine the OCR'd PDF segments into a single PDF.
        """
        combined_pdf_path = os.path.join(self.output_folder, f"{timestamp}_combined_OCR.pdf")
        pdf_writer = PyPDF2.PdfWriter()

        for segment_path in ocr_segments:
            pdf_reader = PyPDF2.PdfReader(segment_path)
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)

        with open(combined_pdf_path, 'wb') as out_pdf_file:
            pdf_writer.write(out_pdf_file)
        
        self.logMessageSignal.emit(f"Combined OCR'd segments into: {combined_pdf_path}")
        return combined_pdf_path

    def split_image(self, image, timestamp):
        """
        Split the image into smaller segments that fit the maximum dimensions for a PDF page.
        """
        segments = []
        for i in range(0, image.height, MAX_PDF_PAGE_HEIGHT):
            segment = image.crop((0, i, image.width, min(i + MAX_PDF_PAGE_HEIGHT, image.height)))
            segment_path = os.path.join(self.output_folder, f"{timestamp}_segment_{i}.png")
            segment.save(segment_path, 'PNG')
            segments.append(segment_path)
        return segments

    def process_ocr_segments(self, segment_paths, timestamp):
        """
        Perform OCR on each image segment and then combine them into a single PDF.
        """
        ocr_segments = []
        for segment_path in segment_paths:
            segment_pdf_path = segment_path.replace('.png', '.pdf')
            self.convert_image_to_pdf(segment_path, segment_pdf_path)
            ocr_segment_path = segment_pdf_path.replace('.pdf', '_OCR.pdf')
            self.ocrmypdf(segment_pdf_path, ocr_segment_path, True)
            ocr_segments.append(ocr_segment_path)
        
        combined_pdf_path = os.path.join(self.output_folder, f"{timestamp}_combined_OCR.pdf")
        self.combine_ocr_segments(ocr_segments)
        return combined_pdf_path
        
    def clean_up_segments(self, segment_paths, ocr_segment_paths):
        """
        Deletes the image segment files and their corresponding OCR PDFs.
        """
        for path in segment_paths + ocr_segment_paths:
            try:
                os.remove(path)
                self.logMessageSignal.emit(f"Deleted file: {path}")
            except OSError as e:
                self.logMessageSignal.emit(f"Error deleting file {path}: {e.strerror}")
                       
    def convert_image_to_pdf(self, image_bytes, pdf_path):
        img = Image.open(image_bytes)
        img_width, img_height = img.size
        # Ensure the image dimensions are within the PDF limits
        if img_width > MAX_PDF_PAGE_WIDTH or img_height > MAX_PDF_PAGE_HEIGHT:
            img = img.resize((min(img_width, MAX_PDF_PAGE_WIDTH), min(img_height, MAX_PDF_PAGE_HEIGHT)), Image.ANTIALIAS)
        
        # Create a PDF canvas and draw the image
        c = canvas.Canvas(pdf_path, pagesize=landscape(letter))
        c.drawImage(ImageReader(img), 0, 0, width=img.width, height=img.height)
        c.save()

    def ocrmypdf(self, input_pdf_path, output_pdf_path, temporary_pdf_created):
        """Runs OCR on a PDF file. Deletes the input PDF if it was created temporarily."""
        try:
            subprocess.run(["ocrmypdf", "--tesseract-downsample-large-images", "--max-image-mpixels", "0", input_pdf_path, output_pdf_path], check=True)
            self.logMessageSignal.emit(f"OCR completed: {output_pdf_path}")
            if temporary_pdf_created:
                os.remove(input_pdf_path)  # Delete the temporary PDF after OCR
                self.logMessageSignal.emit(f"Deleted the temporary PDF: {input_pdf_path}")
        except subprocess.CalledProcessError as e:
            self.logMessageSignal.emit(f"OCRmypdf failed: {str(e)}")
            
    def swipeScreen(self):
    
        # Check if screen_height or screen_width is not defined
        if not hasattr(self, 'screen_height') or not hasattr(self, 'screen_width'):
            self.getScreenInfo()  # Call getScreenInfo to set screen_height and screen_width
    
        # Retrieve swipe direction
        direction = self.scrollCombo.currentText()
        # Retrieve swipe speed from the swipeSpeedComboBox
        duration = int(self.swipeSpeedComboBox.currentText())
    
        swipe_distance = self.screen_height // 4.5
        swipe_start_x = self.screen_width // 2
        swipe_end_x = swipe_start_x

        # Get duration from the combo box
        duration = int(self.swipeSpeedComboBox.currentText())

        # Calculate swipe_start_y and swipe_end_y based on direction
        if direction.upper() == "UP":
            swipe_start_y = int(self.screen_height * 0.5 + swipe_distance / 2)
            swipe_end_y = int(self.screen_height * 0.5 - swipe_distance / 2)
        elif direction.upper() == "DOWN":
            swipe_start_y = int(self.screen_height * 0.5 - swipe_distance / 2)
            swipe_end_y = int(self.screen_height * 0.5 + swipe_distance / 2)
        else:
            self.logMessageSignal.emit(f"Invalid swipe direction: {direction}. Swipe aborted.")
            return

        # Perform the swipe action with specified duration
        subprocess.run([adb_path, 'shell', 'input', 'touchscreen', 'swipe',
                        str(swipe_start_x), str(swipe_start_y),
                        str(swipe_end_x), str(swipe_end_y), str(duration)], check=True)
        # Adjust sleep time as needed, considering the swipe duration
        time.sleep(max(duration / 1000.0, 1))  # Ensure there's at least a 1-second wait for stability

    def getScreenInfo(self):
        try:
            # Execute a shell command to get the screen resolution of the connected Android device
            self.screen_resolution = subprocess.getoutput(f"{adb_path} shell wm size")
            # Parse the resolution output to extract width and height as integers
            self.screen_width, self.screen_height = map(int, self.screen_resolution.split(':')[1].strip().split('x'))
            # Execute a shell command to get the Android version of the connected device
            self.android_version = subprocess.getoutput(f"{adb_path} shell getprop ro.build.version.release")

        except Exception as e:
            # If there is any error (e.g., no device connected), log an error message
            self.logMessageSignal.emit(f"Error retrieving screen info: {str(e)}")
            # You could also handle specific actions here, like disabling certain features or informing the user

    def isDuplicateScreenshot(self, current_image, prev_hash):
        current_hash = imagehash.dhash(current_image)
        if prev_hash is not None and (current_hash - prev_hash) < 5:  # Adjust threshold as needed
            return True, None  # Indicating a duplicate was found
        return False, current_hash
        
    def startAutoScrollScreenshots(self):
        self.lastAction = "autoscroll"  # Set the last action as autoscroll
        # Clear previous session's screenshots
        self.autoscroll_screenshot_paths.clear()
        direction = self.scrollCombo.currentText()
        self.getScreenInfo()  # Retrieves screen size and Android version
        self.autoScrollAndTakeScreenshots(direction)
        
        # After autoscroll screenshots are taken, check for post-processing option
        postProcessOption = self.postCombo.currentText()
        if postProcessOption == 'Crop':
            # Automatically initiate the bulk image crop process
            self.bulkImageCropPostAutoscroll()
        elif postProcessOption == 'Crop + Stitch':
            # Perform cropping first
            self.bulkImageCropPostAutoscroll()
            # Then perform stitching on the cropped images
            self.performStitching(self.autoscroll_screenshot_paths)

    def autoScrollAndTakeScreenshots(self, direction):
        # Retrieve screen information such as resolution and Android version
        self.getScreenInfo()

        # Initialize variables for tracking screenshots and duplicates
        prev_hash = None
        screenshot_count = 0
        duplicate_detected = False
        
        # Determine if scrolling should be infinite or a fixed number of times
        scroll_count_value = self.scrollCountComboBox.currentText()
        infinite_scroll = scroll_count_value == "Infinite"
        scroll_count = int(scroll_count_value) if not infinite_scroll else float('inf')

        # Retrieve the delay between swipes from the combo box
        scrollDelay = float(self.scrollDelayComboBox.currentText())
        
        # Start taking screenshots and swiping through screens
        try:
            while not duplicate_detected and (infinite_scroll or screenshot_count < scroll_count):
                # Attempt to take a screenshot
                current_image = self.takeScreenshot()
                if not current_image:
                    # If taking a screenshot failed (current_image is None), exit the loop
                    break

                # Check for duplicate screenshots indicating the end of scrollable content
                duplicate_detected, prev_hash = self.isDuplicateScreenshot(current_image, prev_hash)
                if duplicate_detected:
                    self.logMessageSignal.emit("Duplicate screenshot detected, stopping autoscroll.")
                    break

                # Increment the screenshot counter and log the action
                screenshot_count += 1
                self.logMessageSignal.emit(f"Screenshot {screenshot_count} taken.")
                
                if screenshot_count < scroll_count:
                    # Perform a swipe action and wait for the specified delay
                    self.swipeScreen()
                    self.logMessageSignal.emit("Swiped screen for next screenshot.")
                    time.sleep(scrollDelay)

            # Emit a final message indicating the end of the autoscroll operation
            self.logMessageSignal.emit(f"Autoscroll screenshots completed. Total screenshots taken: {screenshot_count}.")
        except Exception as e:
            # If an error occurs, log the error and exit the loop
            self.logMessageSignal.emit(f"Error during autoscroll: {str(e)}")
   
        
    def bulkImageCrop(self):
        fileNames, _ = QFileDialog.getOpenFileNames(self, "Select Images for Cropping", self.output_folder, "Images (*.png *.jpg *.jpeg)")
        if fileNames:
            roi_coordinates = self.select_roi_manually(fileNames[0])
            if roi_coordinates:
                output_folder = os.path.dirname(fileNames[0])
                for idx, filePath in enumerate(fileNames):
                    self.crop_screenshot(filePath, roi_coordinates, output_folder)
    
    def resize_image_to_display(self, image):
        """
        Resize an image to fit the screen's vertical resolution while maintaining aspect ratio,
        accounting for the taskbar height.
        """
        taskbar_buffer = 200  # Adjust this value as needed to account for taskbar and window title bar
        screen_height = QApplication.primaryScreen().size().height() - taskbar_buffer  # Subtract buffer
        height, width = image.shape[:2]
        scale = screen_height / height if screen_height < height else 1  # Only scale down if necessary
        new_width = int(width * scale)
        new_height = int(height * scale)
        resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return resized_image

    def select_roi_manually(self, image_path):
        """
        Opens an image, allows the user to manually select a Region of Interest (ROI) by drawing
        a rectangle around it, and returns the ROI coordinates.
        """
        # Emit instructions to the user before starting the ROI selection
        self.logMessageSignal.emit("Select a ROI and then press SPACE or ENTER button!")
        self.logMessageSignal.emit("Cancel the selection process by pressing c button!")
        img = cv2.imread(image_path)
        resized_img = self.resize_image_to_display(img)
        r = cv2.selectROI("Select ROI", resized_img, fromCenter=False, showCrosshair=True)
        cv2.destroyWindow("Select ROI")
        scaling_factor = img.shape[1] / resized_img.shape[1]
        roi = tuple([int(x * scaling_factor) for x in r])
        if roi[2] > 0 and roi[3] > 0:
            self.logMessageSignal.emit(f"ROI coordinates selected: {roi}")
            return roi
        else:
            self.logMessageSignal.emit("No valid ROI selected.")
            return None

    def crop_screenshot(self, image_path, roi_coordinates, output_folder):
        """
        Crop the screenshot based on the ROI coordinates and save it with '_cropped' appended to the original filename,
        maintaining the original file extension.
        """
        # Load the image
        img = cv2.imread(image_path)
        
        # Crop the screenshot based on ROI coordinates
        cropped_img = img[roi_coordinates[1]:roi_coordinates[1]+roi_coordinates[3], roi_coordinates[0]:roi_coordinates[0]+roi_coordinates[2]]
        
        # Extract the original filename without the file extension and the extension itself
        original_filename_without_ext, original_ext = os.path.splitext(os.path.basename(image_path))
        
        # Construct the new filename by appending '_cropped' to the original filename and keeping the original extension
        cropped_image_name = f"{original_filename_without_ext}_cropped{original_ext}"
        
        # Save the cropped screenshot with the new filename in the specified output folder
        cropped_image_path = os.path.join(output_folder, cropped_image_name)
        cv2.imwrite(cropped_image_path, cropped_img)
        
        self.logMessageSignal.emit(f"Cropped screenshot saved to {cropped_image_path}")
        
        return cropped_image_path
        
    def bulkImageCropPostAutoscroll(self):
        """
        Automatically selects screenshots taken during the current autoscroll session for cropping
        and updates the paths to point to the cropped images.
        """
        if not self.autoscroll_screenshot_paths:
            self.logMessageSignal.emit("No autoscroll screenshots available for cropping.")
            return

        # Select ROI from the first screenshot for cropping
        roi_coordinates = self.select_roi_manually(self.autoscroll_screenshot_paths[0])
        if roi_coordinates:
            cropped_paths = []  # Initialize a list to store paths of cropped images
            for filePath in self.autoscroll_screenshot_paths:
                cropped_image_path = self.crop_screenshot(filePath, roi_coordinates, self.output_folder)
                if cropped_image_path:
                    cropped_paths.append(cropped_image_path)
            
            # Update autoscroll_screenshot_paths to point to the cropped images
            self.autoscroll_screenshot_paths = cropped_paths
        
    def get_merge_image_based_on_template(self, image_paths, stitchDirection):
        images = [cv2.imread(img_path) for img_path in image_paths]

        # Check if all images are loaded successfully
        if any(img is None for img in images):
            self.logMessage("Error loading one or more images.")
            return None

        # Initialize variables for the result image
        max_width = max(image.shape[1] for image in images)
        result = None
        current_y = 0
        
        for i in range(len(images)):
            # Convert image to grayscale for template matching
            gray_image = cv2.cvtColor(images[i], cv2.COLOR_BGR2GRAY)
            
            if i == 0:  # First image is just copied to the result image
                result = images[i]
                current_y += images[i].shape[0]
                continue
            
            # Use the last part of the previous result as the template
            overlap_size = 50  # You can adjust this value
            template = cv2.cvtColor(result[-overlap_size:], cv2.COLOR_BGR2GRAY)
            match = cv2.matchTemplate(gray_image, template, cv2.TM_CCOEFF_NORMED)
            _, _, _, max_loc = cv2.minMaxLoc(match)
            
            # Calculate where the new image should be placed
            y_start = max_loc[1] + overlap_size
            if y_start < 0:
                self.logMessage("Error with template matching.")
                return None

            # Stitch the new image
            stitch_height = images[i].shape[0] - y_start
            new_result_height = current_y + stitch_height
            if result is None or new_result_height > result.shape[0]:
                # Increase the result image size if needed
                new_result = np.zeros((new_result_height, max_width, 3), dtype=np.uint8)
                new_result[:current_y, :max_width] = result
                result = new_result
            
            result[current_y:current_y + stitch_height, :images[i].shape[1]] = images[i][y_start:]
            current_y += stitch_height
        
        # Crop the result image to remove any unused space
        result_trimmed = result[:current_y]

        # Save the stitched image
        output_path = os.path.join(self.output_folder, f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_stitched.png")
        cv2.imwrite(output_path, result_trimmed)

        return output_path
    
       
    def onStitchButtonClick(self):
        fileNames, _ = QFileDialog.getOpenFileNames(self, "Select Cropped Images for Stitching", self.output_folder, "Images (*.png *.jpg *.jpeg)")
        if not fileNames:
            self.logMessageSignal.emit("No images selected for stitching.")
            return
        
        self.logMessageSignal.emit(f"{len(fileNames)} images selected for stitching.")
        self.performStitching(fileNames)

    def performStitching(self, imagePaths):
        self.logMessageSignal.emit("Sorting images by datetime...")
        sorted_fileNames = self.sort_images_by_datetime(imagePaths)
        
        if sorted_fileNames:
            self.logMessageSignal.emit("Images sorted.")
            stitchDirection = None
            
            # Determine stitch direction based on the last action
            if self.lastAction == "autoscroll":
                # Use the autoscroll direction for stitching
                stitchDirection = "DOWN" if "Screenshots (Autoscroll UP)" in self.scrollCombo.currentText() else "UP"
            elif self.lastAction == "manual_stitch":
                # Use the manual stitch direction
                stitchDirection = self.directionCombo.currentText()

            # Check the determined stitch direction and adjust the order of images if necessary
            if stitchDirection == 'UP':
                self.logMessageSignal.emit("Reversing image order for 'UP' stitching direction.")
                sorted_fileNames.reverse()

            self.logMessageSignal.emit(f"Starting stitching process for {len(sorted_fileNames)} images, direction: {stitchDirection}.")
            stitched_image_path = self.get_merge_image_based_on_template(sorted_fileNames, stitchDirection)
            if stitched_image_path:
                self.logMessageSignal.emit(f"Stitched image saved to: {stitched_image_path}")
            else:
                self.logMessageSignal.emit("Stitching failed.")
        else:
            self.logMessageSignal.emit("Failed to sort images. Aborting stitching process.")
            
        if stitched_image_path:  # Check if the stitched image was saved successfully
            self.logMessageSignal.emit(f"Stitched image saved to: {stitched_image_path}")
            
            # Clean up cropped images after successful stitching
            if 'Crop + Stitch' in self.postCombo.currentText():
                # Assuming you have a list of paths to the temporary cropped images
                self.clean_up_cropped_images(self.autoscroll_screenshot_paths)
        else:
            self.logMessageSignal.emit("Stitching failed.")
            
    def extract_datetime_from_filename(self, filename):
        basename = os.path.basename(filename)  # Get the filename without the path
        datetime_part = basename.split('_cropped')[0]  # Extract the datetime part before '_cropped'
        datetime_part = datetime_part.rsplit('.', 1)[0]  # Further ensure any extension is removed
        return datetime.datetime.strptime(datetime_part, "%Y-%m-%d_%H-%M-%S")
        
    def sort_images_by_datetime(self, imagePaths):
        try:
            sorted_imagePaths = sorted(imagePaths, key=self.extract_datetime_from_filename)
            return sorted_imagePaths
        except Exception as e:
            self.logMessageSignal.emit(f"Error sorting images: {str(e)}")
            return imagePaths  # Return the original list if sorting fails
            
    def clean_up_cropped_images(self, cropped_image_paths):
        """
        Deletes temporary cropped images used for stitching.
        """
        for path in cropped_image_paths:
            try:
                os.remove(path)
                self.logMessageSignal.emit(f"Deleted temporary cropped image: {path}")
            except Exception as e:
                self.logMessageSignal.emit(f"Error deleting temporary cropped image {path}: {str(e)}")
                
                
    def getScreenInfo(self):
        try:
            # Example command to get screen size (you'll need to adjust this to your requirements)
            output = subprocess.check_output([adb_path, 'shell', 'wm', 'size']).decode('utf-8')
            resolution = output.split()[-1]
            self.screen_width, self.screen_height = map(int, resolution.split('x'))
        except Exception as e:
            self.logMessageSignal.emit(f"Error retrieving screen info: {str(e)}")
            # Default values in case of error
            self.screen_width = 1080  # Default width
            self.screen_height = 1920  # Default height
            
    def dump_ui_xml_and_save(self, local_path):
        """Dumps the UI hierarchy and saves it to the local machine without using device storage."""
        command = [adb_path, 'exec-out', 'uiautomator', 'dump', '--compressed', '/dev/tty']
        try:
            with open(local_path, "wb") as f:
                f.write(subprocess.check_output(command))
            self.logMessageSignal.emit(f"UI XML dumped to {local_path}")
        except subprocess.CalledProcessError as e:
            self.logMessageSignal.emit(f"Failed to dump UI XML: {str(e)}")
        # Wait for a short period to ensure file is written
        time.sleep(2)  # Waits for 2 seconds

    def extract_generic_text_from_ui_dump(self, ui_dump_path, output_text_file):
        """Extracts text from the UI dump XML without relying on a specific resource-id and writes it to a text file."""
        try:
            self.logMessageSignal.emit(f"Starting generic text extraction from {ui_dump_path}...")
            import xml.etree.ElementTree as ET

            with open(ui_dump_path, "r", encoding="utf-8") as file:
                xml_content = file.read()
            
            xml_start_pos = xml_content.find("<hierarchy")
            xml_end_pos = xml_content.rfind("</hierarchy>") + len("</hierarchy>")
            if xml_start_pos == -1 or xml_end_pos == -1:
                self.logMessageSignal.emit("Failed to find the XML hierarchy data.")
                return
            
            clean_xml_content = xml_content[xml_start_pos:xml_end_pos]
            root = ET.fromstring(clean_xml_content)
            all_texts = [elem.attrib["text"] for elem in root.iter() if "text" in elem.attrib and elem.attrib["text"].strip()]
            
            if all_texts:
                with open(output_text_file, "w", encoding="utf-8") as text_file:
                    for text in all_texts:
                        text_file.write(text + "\n")
                self.logMessageSignal.emit(f"Text extracted to {output_text_file}")
                # After successfully writing texts, delete the XML file
                os.remove(ui_dump_path)
                self.logMessageSignal.emit(f"UI XML file deleted: {ui_dump_path}")
            else:
                self.logMessageSignal.emit(f"No text found in {ui_dump_path}.")
        except ET.ParseError as pe:
            self.logMessageSignal.emit(f"Failed to parse XML: {pe}")
        except FileNotFoundError:
            self.logMessageSignal.emit(f"File not found: {ui_dump_path}")
        except Exception as e:
            self.logMessageSignal.emit(f"An error occurred: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SCRCPYULTRA()
    ex.show()
    sys.exit(app.exec_())