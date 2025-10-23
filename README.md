# Test Cycle Scammer - Web Version

This project has been updated with a modern web-based UI using Flask and JavaScript.

## Installation

Install the required dependencies:

```bash
pip3 install flask matplotlib
```

## Running the Application

1. Start the web server:
```bash
python3 web_app.py
```

2. Open your browser and go to:
```
http://localhost:5000
```

## Features

- 📁 **Interactive Folder Browser**: Browse and select folders directly in the web interface
- ✨ **Modern UI**: Clean, responsive design with gradient backgrounds
- 📊 **Inline Results**: View all plots directly in the browser
- 🎯 **Easy Selection**: Click to select folders, double-click to navigate
- 🗑️ **Quick Management**: Remove selected folders with one click

## How to Use

1. Browse through folders using the file browser
2. Click on folders to select them (you need exactly 5)
3. Selected folders appear as chips below the browser
4. Click "Analyze Data" when you have 5 folders selected
5. View the generated plots for each channel directly in the browser

## Original Tkinter Version

The original Tkinter version is still available in `main.py`.
