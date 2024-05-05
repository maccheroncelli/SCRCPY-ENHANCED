# SCRCPY-ULTRA

## Description
SCRCPY-ULTRA enhances the functionality of the original SCRCPY application. Autoscrolling, OCR of screenshots, cropping of screenshots, and image stitching...

To leverage the full functionality of SCRCPY-ULTRA, including screen recording and mirroring, place the script in the same directory as your SCRCPY installation. 
This setup ensures that SCRCPY-ULTRA can utilize scrcpy's capabilities directly.

## Installation

### Setup
1. Download SCRCPY and extract to a directory - https://github.com/Genymobile/scrcpy/releases
2. Download and install Tesseract (and foreign lanaguages via the installer) - https://github.com/UB-Mannheim/tesseract/wiki
3. Add the tesseract install directory (C:\Program Files\Tesseract-OCR) to Windows Environment variables - Edit 'Path' and add a new line for Tesseract.
4. Download and install Ghostscript (Ghostscript AGPL Release) - https://www.ghostscript.com/releases/gsdnld.html
5. Download the `SCRCPY-ULTRA' script and place it into the SCRCPY directory.
6. Install required Python packages:
   ```sh
   pip install PyQt5 opencv-python PyPDF2 pyautogui numpy pillow reportlab imagehash ocrmypdf
   ```
7. Run the script using Python:
   ```sh
   python SCRCPY-ULTRA-VX.X.py
   ```
8. Android device - Enable **Developer Mode** by going to Settings > About phone and tapping Build number 7 times.
9. Android device - Enable **USB Debugging** in Developer options.
10. On some devices (Xiaomi and possibly others), enable **USB debugging (Security Settings)** (this is an item different from USB debugging) to control it using a keyboard and mouse.
11. Connect phone to computer and accept trust messages.
12. All generated files saved to a directory within the scrcpy install path **..\AndroidScreenOutput**
  
## Features

- **SCRCPY Functionality**: 
   - Screen Mirroring
   - Screen recording: Commences a recording in MP4 format. File will be saved on exit as "%Y-%m-%d_%H-%M-%S", (Example: 2024-05-05_07-14-42.mp4)
     
- **Screenshot Tool**:
   - Offers the ability to take screenshots of the connected device.
   - Uses ADB to save a PNG file with the filename as "%Y-%m-%d_%H-%M-%S", (Example: 2024-05-05_07-14-42.png)
     
- **OCR Capabilities**
   -  When enabled, every screenshot will be converted to a black and white PDF document, and then OCR'd with Tessract.  High contrast PDF produces more accurate results.  Also performed for autoscrolling screenshots if selected.
   -  Screen Dump (uiAutomate) **Experimental** : Included for the use case that tesseract cannot work with certain foreign languages. Characters on screen will be attepmted to tbe dumped to a txt file.  Not all Apps work                 (Messenger does not, but signal and others do..)
   
- **Autoscroll**:
   - Automates scrolling on the connected device
   - Swipe Direction: Direction of your virtual finger swipe.
   - Swipe Speed: How forceful the swipe is and might need adjustment dependin on chat app.  Use the **Test Swipe Speed** button to perform a one time swipe to make sure you dont miss content.
   - Swipe count:
      - **Infinite** swipe count will continue scrolling until the top or the bottom of the chat has been reached.  DHash is used to determine if the last two images are the same to stop scolling.
      - Otherwise a set number of swipes can be selected to prevent  capturing too much unnessicary data.
   - Swipe Delay: Allows the user to add a delay before hte screenshot is taken.  Ideal for when dynamic content is loaded like pictures in a chat.
   - Post Processing:
      - **Crop**
         - After the scrollin screenshots have been performed, a window will appear for the user to select the ROI (Region of Interest).  You do this by using the mouse to select the exact chat convewrsation window and                         discarding both the header and the footer of the chat.  Hold down the mouse after the initial start point and drag out a rectangle.  Unclick and then press **ENTER**. All images will be cropped the same.  The                        reason for this is to optimise the stitch operation by removing necessary
      - **Crop and Stitch**
         - Performs the above **crop** operation and then stiches all the images together.
           
   - **Manual OCR** - User can select files via a dialog box to attempt to OCR.
   - **Manual Crop** - User can select files via dialog box to Crop.
   - **Manual Stitch** - User can select files via dialog box to crop, but must give the original swipe direction of the images to achieve a successful stitch.  Try both if unknown...

## Contributing

Contributions to SCRCPY-ULTRA are welcome. Here are ways you can contribute:
- Reporting bugs
- Suggesting enhancements
- Submitting pull requests for new features or bug fixes

For major changes, please open an issue first to discuss what you would like to change.

## Screenshot
![image](https://github.com/maccheroncelli/SCRCPY-ULTRA/assets/154501937/2ad1eb8f-2668-481b-808d-ff9f9f9b1457)

