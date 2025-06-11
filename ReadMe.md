# Sunspot Levels Adjuster

A native desktop application built with Flet and Pillow that allows users to upload an image, adjust levels (black point, white point, gamma) to increase contrast, and export the adjusted image.

## Features

* Upload photo via file picker
* Adjust Black Point, White Point, and Gamma sliders with live preview
* Export adjusted image as PNG with timestamped filename

## Requirements

* Python 3.7 or newer
* [Flet](https://pypi.org/project/flet/)
* [Pillow](https://pypi.org/project/Pillow/)

## Installation

Install dependencies using pip:

```bash
pip install flet pillow
```

## Usage

Run the application:

```bash
python SunImageTool.py
```

1. A native desktop window will open.
2. Click **Upload Photo** to select an image file.
3. Use the  **Black Point** ,  **White Point** , and **Gamma** sliders to adjust the image levels with live preview.
4. Click **Export Photo** to save the adjusted image as a PNG in the current directory (filename is timestamped).

## Project Structure

```
SunImageTool.py    # Main application script
README.md          # Project documentation
```

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests for bug fixes and new features.

## License

This project is licensed under the MIT License.
