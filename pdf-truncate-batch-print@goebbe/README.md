Truncate and batch-print PDF(s)
==============================

Cut PDF(s) pages at the start and from the end and batch-print them.

DESCRIPTION
-----------

This action allows you to cut the same number of pages from PDF(s) at the start and from the end 
and batch-print (mass-print) the resulting truncated PDF(s) with the printer of your choice. 

Use case: Batch processing when printing a large number of PDFs without cover-letter(s) and small print(s).

Example: Printing a large number of similar PDF-invoices. These PDFs all start with a cover-letter
and all end with two pages of the small print. The cover-letter and the small print should not be printed. 
This action allows to batch print the pages between the cover-letter and the small print and only print 
the interesting part (the actual invoices).

If `printer-driver-cups-pdf` is installed, it is also possible to print to PDF, to easily obtain truncated PDF(s).

INSTALLATION
------------
The easiest way to install a Nemo action is via "Menu > System Settings > Actions": 

1. Download: In "Actions", go to "Download" > "Refresh" the list of available actions > select the action > press the download button
2. Enable: In "Actions", go to "Manage" > select the new action > press "+" to enable
3. It may be necessary to restart the Nemo file-manager


USAGE
------------

1. Select one or more PDF-files:
Right click on the selected PDF(s) and choose "Truncate and batch-print PDF(s)" from the context menu.
Note that this menu entry is only visible if the selected file(s) are actually PDF(s).
2. Type the number of pages to be truncated, at the start and from the end.
3. Choose the printer and choose between one-sided and two-sided printing.
Now the batch-print will start. 
The same truncation will be applied to all PDF(s) during the batch-print. 


DEPENDENCIES
------------

The following packages/ commands must be available:

* `zenity` for a simple GUI
* `lpr` for command line printing (part of cups)
* `lpstat`to get the available printers (part of cups)
* `pdfinfo` to get the total number of pages of a PDF(s) (part of poppler-utils)

On Debian based distributions,to install the required packages in the terminal, type:
sudo apt install zenity cups poppler-utils 
