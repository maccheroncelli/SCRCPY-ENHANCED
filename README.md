# SCRCPY-ULTRA

## Description
SCRCPY-ULTRA enhances the functionality of the original SCRCPY application. Autoscrolling, OCR of screenshots, cropping of screenshots, and image stitching...

To leverage the full functionality of SCRCPY-ULTRA, including screen recording and mirroring, place the script in the same directory as your SCRCPY installation. 
This setup ensures that SCRCPY-ULTRA can utilize scrcpy's capabilities directly.

## Installation

### Setup
1. Download SCRCPY and extract to a directory - https://github.com/Genymobile/scrcpy/releases
2. Download and install Tesseract - https://github.com/UB-Mannheim/tesseract/wiki
3. Add the tesseract install directory (C:\Program Files\Tesseract-OCR) to Windows Environment variables - Edit 'Path' and add a new line for Tesseract.
4. Download and install Ghostscript (Ghostscript AGPL Release) - https://www.ghostscript.com/releases/gsdnld.html
5. Download the `SCRCPY-ULTRA' script and place it into the SCRCPY directory.
6. Install required Python packages:
   ```sh
   pip install PyQt5 opencv-python opencv-python-headless PyPDF2 pyautogui numpy pillow reportlab imagehash ocrmypdf
   ```
7. Run the script using Python:
   ```sh
   python SCRCPY-ULTRA-VX.X.py
   ```
8. Android device - Enable **Developer Mode** by going to Settings > About phone and tapping Build number 7 times.
9. Android device - Enable **USB Debugging** in Developer options.
10. On some devices (Xiaomi and possibly others), enable **USB debugging (Security Settings)** (this is an item different from USB debugging) to control it using a keyboard and mouse.
11. Connect phone to computer and accept trust messages.
  
## Features

- **SCRCPY Functionality**: Enables users to start SCRCPY directly through the interface without command line interaction, simplifying the process of screen mirroring and device control.
- **Screenshot Tool**: Offers the ability to take screenshots of the connected device. It supports Optical Character Recognition (OCR) to recognize text within screenshots, which can then be used to create searchable PDF documents.
- **Autoscroll**: Automates scrolling on the connected device, with customizable direction, speed, and count, ideal for capturing content.
- **OCR Capabilities**: Integrated OCR function that can be manually triggered, allowing the extraction of text from images or screenshots.
- **Image Post-Processing**: Includes options for post-processing of images, such as cropping and stitching, to refine the results before saving or utilizing them further.
- **Image Stitching**: Premier feature, provides the ability to stitch images together in a specified direction, which is particularly useful for creating a continuous image sequence from multiple screenshots.

## Contributing

Contributions to SCRCPY-ULTRA are welcome. Here are ways you can contribute:
- Reporting bugs
- Suggesting enhancements
- Submitting pull requests for new features or bug fixes

For major changes, please open an issue first to discuss what you would like to change.

## Screenshot
![image](https://github.com/maccheroncelli/SCRCPY-ULTRA/assets/154501937/2ad1eb8f-2668-481b-808d-ff9f9f9b1457)

