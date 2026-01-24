### 0.0.1

* Initial release

### 0.1.0

* new features:

1. PDF to Image Conversion
    * Added a feature that allows converting PDFs into image formats such as PNG, JPG, and TIFF.
    * Users can specify additional parameters like resolution (DPI), the range of pages to convert, and the image format.
    * Default values will be applied if the user leaves fields empty.

### 0.2.0

* New Features:

1. Merge to PDF: Added the ability to combine multiple selected images into a single PDF document.
2. Animated GIF Creation: Added the ability to merge multiple images into a single animated GIF.
3. JPEG XL Support: Added support for converting images to and from the JPEG XL (.jxl) format.
4. Better SVG Tracing: Added VTracer to convert raster images into vector graphics
5. Overwrite Protection: The script now checks if a filename exists and automatically renames the output (e.g., file_1.png) to prevent accidental data loss.
6. Error Reporting: Added a detailed error log window that displays specific failure messages if a conversion is unsuccessful.

* Improvements:

1. Dependency Checking: The script now verifies that all required tools (e.g., zenity, img2pdf) are installed before running.
2. Code Refactoring: Major cleanup of the codebase, moving logic into modular functions and improving localization handling.
3. Skipped File Summary: Users are now notified with a list of specific files that were skipped due to unsupported formats.