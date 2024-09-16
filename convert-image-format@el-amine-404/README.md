# Convert Image Format

Easily convert image files to various formats or turn PDF files into images directly from the Nemo file manager.

## DESCRIPTION

This action allows you to:
- Convert single or multiple image files to a variety of formats (currently 15 formats and their variants).
- Convert PDF files into images where each page is converted into an image. The action will generate a folder named after the PDF file in the current directory, and each page's image will be named using the format `pg_<page_number>.<extension>`.
Example: A PDF file named document.pdf will generate a folder document, containing images pg_1.png, pg_2.png, etc.

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

The following program must be installed for this action to work:

| DEPENDENCY                                                                               | INSTALLATION                            |
| ---------------------------------------------------------------------------------------- | --------------------------------------- |
| [convert](https://imagemagick.org/) (from ImageMagick)                                   | `sudo apt-get install -y imagemagick`   |
| [zenity](https://help.gnome.org/users/zenity/stable/)                                    | `sudo apt-get install -y zenity`        |
| [file](https://man7.org/linux/man-pages/man1/file.1.html)                                | `sudo apt-get install -y file`          |
| [rsvg-convert](https://manpages.ubuntu.com/manpages/kinetic/en/man1/rsvg-convert.1.html) | `sudo apt-get install -y librsvg2-bin`  |
| [pdftoppm](https://linux.die.net/man/1/pdftoppm)                                         | `sudo apt-get install -y poppler-utils` |
| [xargs](https://linux.die.net/man/1/xargs)                                               | `sudo apt-get install -y findutils`     |

or download the 6 in one go:

```sh
sudo apt-get update
sudo apt-get install -y imagemagick zenity file librsvg2-bin poppler-utils findutils
```

## CONTRIBUTING

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request on the [project's GitHub repository](https://github.com/linuxmint/cinnamon-spices-actions).
