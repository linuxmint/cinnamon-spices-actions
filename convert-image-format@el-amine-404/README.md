# Convert Image Format

Easily convert image files to various formats or turn PDF files into images directly from the Nemo file manager.

## DESCRIPTION

This action allows you to:
- Convert single or multiple image files to a variety of formats (currently 15 formats and their variants).
- Convert PDF files into images where each page is converted into an image. The action will generate a folder named after the PDF file in the current directory, and each page's image will be named using the format `pg_<page_number>.<extension>`. Example: A PDF file named document.pdf will generate a folder document, containing images pg_1.png, pg_2.png, etc.
- Select multiple images and combine them into a single PDF document.

## Supported formats

### Image Conversion

| Format                                                             | Description                             |
| ------------------------------------------------------------------ | --------------------------------------- |
| *.apng                                                             | Animated Portable Network Graphics      |
| *.avif                                                             | AV1 Image File Format                   |
| *.bmp                                                              | Bitmap                                  |
| *.gif                                                              | Graphics Interchange Format             |
| *.heic                                                             | High Efficiency Image Coding            |
| *.heif                                                             | High Efficiency Image Format            |
| \*.ico, \*.cur                                                     | Microsoft Icon                          |
| \*.jpg, \*.jpeg, \*.pjpeg, \*.pjp, \*.jpe, \*.jfi, \*.jfif, \*.jif | JPEG (Joint Photographic Experts Group) |
| \*.jp2, \*.j2k                                                     | JPEG 2000 Image                         |
| *.jxl                                                              | JPEG XL Image Coding System             |
| *.pdf                                                              | Portable Document Format                |
| *.png                                                              | Portable Network Graphics               |
| *.svg                                                              | plaintext Scalable Vector Graphics      |
| *.svgz                                                             | compressed Scalable Vector Graphics     |
| \*.tiff, \*.tif                                                    | Tagged Image File Format                |
| *.webp                                                             | Web Picture format                      |

### PDF to Image Conversion


| Format | Description                             |
| ------ | --------------------------------------- |
| *.png  | Portable Network Graphics               |
| *.jpg  | JPEG (Joint Photographic Experts Group) |
| *.tiff | Tagged Image File Format                |

The tool also supports custom resolution (DPI) and allows specifying the range of pages to convert from the PDF.

## DEPENDENCIES

### Core

These tools are essential for the script to function. Most Linux distributions have `file`, `findutils`, and `coreutils` installed by default.

| TOOL                                                                                                   | INSTALLATION                            |
| :----------------------------------------------------------------------------------------------------- | :-------------------------------------- |
| **[zenity](https://gitlab.gnome.org/GNOME/zenity)** (GUI Dialogs)                                      | `sudo apt-get install -y zenity`        |
| **[notify-send](https://manpages.ubuntu.com/manpages/trusty/man1/notify-send.1.html)** (Notifications) | `sudo apt-get install -y libnotify-bin` |
| **[convert](https://imagemagick.org/)** (ImageMagick)                                                  | `sudo apt-get install -y imagemagick`   |
| **[pdftoppm](https://linux.die.net/man/1/pdftoppm)** (Poppler)                                         | `sudo apt-get install -y poppler-utils` |
| **[img2pdf](https://gitlab.mister-muffin.de/josch/img2pdf)** (PDF Merging)                             | `sudo apt-get install -y img2pdf`       |
| **[file](https://man7.org/linux/man-pages/man1/file.1.html)**                                          | `sudo apt-get install -y file`          |
| **[xargs](https://linux.die.net/man/1/xargs)** (Findutils)                                             | `sudo apt-get install -y findutils`     |
| **[cut](https://man7.org/linux/man-pages/man1/cut.1.html)** (Coreutils)                                | `sudo apt-get install -y coreutils`     |
| **[gzip](https://www.gnu.org/software/gzip/)** (SVGZ Compression)                                      | `sudo apt-get install -y gzip`          |

to install all of them at once, run:

```sh
sudo apt-get update
sudo apt-get install -y imagemagick zenity libnotify-bin img2pdf poppler-utils file findutils coreutils gzip
```

### Format Support & Optional Tools

Install these to enable specific file format conversions

| SUPPORT / FEATURE             | TOOL                                                                                 | INSTALLATION                                 |
| :---------------------------- | :----------------------------------------------------------------------------------- | :------------------------------------------- |
| **JPEG XL Support**           | [cjxl / djxl](https://github.com/libjxl/libjxl)                                      | `sudo apt-get install -y libjxl-tools`       |
| **AVIF Support**              | [avifenc](https://github.com/AOMediaCodec/libavif)                                   | `sudo apt-get install -y libavif-bin`        |
| **HEIC Conversion**           | [heif-convert](https://manpages.ubuntu.com/manpages/focal/man1/heif-convert.1.html)  | `sudo apt-get install -y libheif-examples`   |
| **HEIF Library**              | [libheif1](https://github.com/strukturag/libheif)                                    | `sudo apt-get install -y libheif1`           |
| **JPEG 2000 Support**         | [libopenjp2-7](https://github.com/uclouvain/openjpeg)                                | `sudo apt-get install -y libopenjp2-7`       |
| **SVG Rasterization**         | [rsvg-convert](https://manpages.ubuntu.com/manpages/bionic/man1/rsvg-convert.1.html) | `sudo apt-get install -y librsvg2-bin`       |
| **SVG Tracing (Recommended)** | [vtracer](https://github.com/visioncortex/vtracer)                                   | `cargo install vtracer`                      |
| **SVG Tracing (fallback)**    | [inkscape](https://gitlab.com/inkscape/inkscape)                                     | `sudo apt-get install -y inkscape`           |
| **SVG Tracing (fallback)**    | [potrace](https://potrace.sourceforge.net/)                                          | `sudo apt-get install -y potrace`            |
| **PDF/PS Backend**            | [gs](https://ghostscript.com/documentation/)                                         | `sudo apt-get install -y ghostscript`        |
| **AVIF Thumbnails**           | [libavif-gdk-pixbuf](https://packages.debian.org/sid/libavif-gdk-pixbuf)             | `sudo apt-get install -y libavif-gdk-pixbuf` |
| **HEIF Thumbnails**           | [heif-gdk-pixbuf](https://packages.debian.org/sid/heif-gdk-pixbuf)                   | `sudo apt-get install -y heif-gdk-pixbuf`    |

to install all of them at once, run:

```sh
sudo apt-get update
sudo apt-get install -y libjxl-tools libavif-bin libheif-examples libheif1 libopenjp2-7 librsvg2-bin inkscape potrace ghostscript libavif-gdk-pixbuf heif-gdk-pixbuf
```

## CONTRIBUTING

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request on the [project's GitHub repository](https://github.com/linuxmint/cinnamon-spices-actions).
