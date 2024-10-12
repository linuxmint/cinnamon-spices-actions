
Create EPUB from files
======================

Provides an easy way to combine together plain text (.txt), markdown (.md),
XHTML (.xhtml), .png, .gif and .jpg files together into an EPUB file. The sequence of
images and text files depends on their filename order, so if you want to have a cover
image and two chapters in your EPUB, have their files named 01-Cover.png, 02-Chapter-1.txt,
and 03-Chapter-2.txt.

Image files:
* .jpg
* .png
* .gif

Text Documents:
* .txt
* .md
* .xhtml

Images (.jpg, .png, .gif) are centered and scaled to use the whole page. If
an image is referenced in one of the text files, then it will be an image that
is part of that text file only and won't be in the sequence of generated pages.

When using plain text files (.txt), two line breaks starts a new paragraph. a 
small subset of markdown is available, specifically the first and second level
heading syntax. If there are no headings found in the file, then the first line
of the file becomes the heading if it is not a paragraph that spans multiple lines. 

.md files are processed by calling the markdown processor, the markdown processor
can be configured to be any markdown engine or script the user wants that can take
as standard input the markdown text, and outputs XHTML to its standard output.
By default the processor is `python -m markdown`.

.xhtml files are included into the EPUB with only a bit of processing, such as
balancing tags and adding a few tags if needed.


Example
-------

An example ebook:

* Have a cover image called 01-cover.jpg
* Have one or more text files 02-chapter-one.txt, 03-chapter-three.txt, etc.

Simply select the files, right click and choose "Create EPUB from files"
to make an EPUB.

Dependencies
------------

Requires Perl 5 with some common libraries, which is usually installed with most linux
distributions.


