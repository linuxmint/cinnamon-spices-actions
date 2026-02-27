REMOVE IMAGE METADATA
================================================================================

Remove EXIF, IPTC, XMP and other metadata from images

DESCRIPTION
-----------

This action allows you to remove all metadata (EXIF, IPTC, XMP, etc.) from image files.

DEPENDENCIES
------------

The following programs must be installed and available:

* `exiftool` - Tool for reading and writing metadata in files

Installation on Linux Mint/Debian/Ubuntu:
```bash
sudo apt install exiftool
```

USAGE
-----

1. Select one or more image files in Nemo
2. Right-click and choose "Remove image metadata"
3. Metadata will be removed from the selected images
4. Original files are overwritten (no backup created)

⚠️  **WARNING**: This action permanently removes ALL metadata from images and overwrites the original files. Make sure you have backups if you need to preserve any information.

SUPPORTED FORMATS
-----------------

**Common Image Formats:**
- JPEG, JPG, PNG, GIF, BMP, TIFF, WEBP

**RAW Camera Formats:**
- Canon: CR2, CR3, CRW
- Nikon: NEF, NRW
- Sony: ARW, SR2, SRF
- Fujifilm: RAF
- Olympus: ORF
- Panasonic: RW2, RAW
- Pentax: PEF, DNG
- Sigma: X3F
- Hasselblad: 3FR, FFF
- Phase One: IIQ
- Mamiya: MEF, MOS
- Kodak: DCR, KDC, K25
- Minolta: MRW
- Samsung: SRW
- Leica: RWL, DNG
- Adobe: DNG (Digital Negative)

**Other Formats:**
- HEIC, HEIF (Apple/iOS formats)
- PSD (Adobe Photoshop)
- AI (Adobe Illustrator - raster data)
- PGF (Progressive Graphics File)

**Total: 50+ image formats supported**

METADATA TYPES REMOVED
----------------------

ExifTool removes all standard metadata types including:
- **EXIF** (Exchangeable Image File Format)
- **IPTC** (International Press Telecommunications Council)
- **XMP** (Extensible Metadata Platform)
- **GPS** (Geolocation data)
- **MakerNotes** (Camera-specific data)
- **ICC Profile** (Color management data)
- **JFIF** (JPEG File Interchange Format)
- **Photoshop IRB** (Image Resource Blocks)
- And many more...

AUTHOR
------

pzim-devdata
