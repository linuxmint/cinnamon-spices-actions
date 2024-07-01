# Convert Image Format

Easily convert image files to various formats directly from the Nemo file manager.

DESCRIPTION
-----------

This action lets you convert a single or multiple image files to the following formats (currently 15 formats and their variants):

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

DEPENDENCIES
------------

The following program must be installed for this action to work:

| DEPENDENCY                                                                               | INSTALLATION                           |
| ---------------------------------------------------------------------------------------- | -------------------------------------- |
| [convert](https://imagemagick.org/) (from ImageMagick)                                   | `sudo apt-get install -y imagemagick`  |
| [zenity](https://help.gnome.org/users/zenity/stable/)                                    | `sudo apt-get install -y zenity`       |
| [file](https://man7.org/linux/man-pages/man1/file.1.html)                                | `sudo apt-get install -y file`         |
| [rsvg-convert](https://manpages.ubuntu.com/manpages/kinetic/en/man1/rsvg-convert.1.html) | `sudo apt-get install -y librsvg2-bin` |

or download the 4 in one go:

```sh
sudo apt-get update
sudo apt-get install -y imagemagick zenity file librsvg2-bin
```

CONTRIBUTING
------------

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request on the [project's GitHub repository](https://github.com/linuxmint/cinnamon-spices-actions).
