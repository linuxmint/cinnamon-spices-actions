"""Detects which archivers are installed and what each one can do.

Mirrors the capability model of the original C/GTK3 prototype
(../archive_action_c/src/archivers.c): every format the dialog can
offer is described by a small capability bitmask, and a format only
becomes selectable if the tool(s) it needs are actually on PATH.
"""

import shutil

FMT_7Z = "7z"
FMT_ZIP = "zip"
FMT_TAR = "tar"
FMT_TAR_GZ = "tar.gz"
FMT_TAR_BZ2 = "tar.bz2"
FMT_TAR_XZ = "tar.xz"
FMT_TAR_ZST = "tar.zst"
FMT_TAR_LZ = "tar.lz"
FMT_TAR_LZO = "tar.lzo"
FMT_TAR_Z = "tar.Z"
FMT_TAR_LZ4 = "tar.lz4"
FMT_RAR = "rar"
FMT_ARJ = "arj"
FMT_ARC = "arc"
FMT_LHA = "lha"
FMT_CPIO = "cpio"
FMT_SHAR = "shar"

# Order the format combo box is populated in.
FORMAT_ORDER = [
    FMT_7Z, FMT_ZIP, FMT_TAR, FMT_TAR_GZ, FMT_TAR_BZ2, FMT_TAR_XZ, FMT_TAR_ZST,
    FMT_TAR_LZ, FMT_TAR_LZO, FMT_TAR_Z, FMT_TAR_LZ4, FMT_RAR,
    FMT_ARJ, FMT_ARC, FMT_LHA, FMT_CPIO, FMT_SHAR,
]

CAP_ENCRYPT = 1 << 0       # password-protect archive contents
CAP_SFX = 1 << 1           # build a self-extracting archive
CAP_RECOVERY = 1 << 2      # embed a recovery record
CAP_HEADER_ENC = 1 << 3    # also encrypt file names, not just contents
CAP_SPLIT = 1 << 4         # split into multiple volumes
CAP_TEST = 1 << 5          # verify integrity via a separate command after creation
CAP_TEST_INLINE = 1 << 6   # verification happens via a creation-time flag instead
CAP_COMPRESSION = 1 << 7   # store/fastest/fast/normal/good/best method
CAP_DICT_SIZE = 1 << 8     # choose the compression dictionary size
CAP_COMMENT = 1 << 9       # embed an archive comment (text or file)
CAP_DEDUP_REFS = 1 << 10   # store identical files as references, not copies
CAP_STORE_MTIME = 1 << 11  # explicit "store modification time" toggle
CAP_STORE_CTIME = 1 << 12  # explicit "store creation time" toggle
CAP_STORE_ATIME = 1 << 13  # explicit "store access time" toggle
CAP_PRESERVE_ATIME = 1 << 14      # don't let archiving change source files' atime
CAP_HIGH_PRECISION_TIME = 1 << 15  # sub-second/timezone-aware timestamps
CAP_APPEND_EXISTING = 1 << 16     # adding to an archive of this name that
                                   # already exists is supported (vs. always
                                   # being replaced)
CAP_FLAT_FILES_ONLY = 1 << 17     # the tool doesn't recurse into directories
                                   # itself, so the file list must be
                                   # expanded to individual files first

# Compression method levels for CAP_COMPRESSION, in dropdown order.
COMPRESS_STORE, COMPRESS_FASTEST, COMPRESS_FAST, COMPRESS_NORMAL, COMPRESS_GOOD, COMPRESS_BEST = range(6)

# Which file timestamp a date filter or "store time" option refers to.
TIME_MODIFICATION, TIME_CREATION, TIME_ACCESS, TIME_ANY = range(4)

# Capability -> real CLI flag reference (see the top-level README for the
# full writeup):
#   CAP_COMPRESSION:   7z -mx{0,1,3,5,7,9} / zip -{0,1,3,6,8,9} / rar -m{0..5}
#   CAP_DICT_SIZE:     7z -m0=lzma2:d=<size> / rar -md<size>
#   CAP_COMMENT:       zip -z (reads from stdin) / rar -z<file>
#   CAP_DEDUP_REFS:    7z -snh (hardlinks only) / rar -oi (any identical content)
#   CAP_STORE_*TIME:   rar -tsm/-tsc/-tsa (no equivalent choice in 7z/zip/tar)
#   CAP_PRESERVE_ATIME: 7z -ssp / rar -tsp
#   CAP_HIGH_PRECISION_TIME: rar -ma5 vs -ma4 (RAR5 stores full-precision
#                            timestamps; RAR4 only 2-second DOS resolution)
#   CAP_APPEND_EXISTING: 7z/zip/rar's "add" already merges into an existing
#                        archive; plain tar switches -cf/-rf on existence;
#                        arj/arc/lha's "a" command was confirmed (via a
#                        real install) to update rather than replace too.
#                        Compressed tar.* (including the lz/lzo/Z/lz4
#                        variants below) genuinely can't be appended to in
#                        place (there's no way to add to a compressed
#                        stream), nor can cpio/shar as we drive them here,
#                        so those stay unset -- ui.py batches into them via
#                        a different mechanism instead (see BATCH_SIZE).
#   CAP_FLAT_FILES_ONLY: arj/arc/lha/cpio/shar -- rather than trust each
#                        one's own recursion support, we always expand
#                        directories to individual files ourselves first,
#                        the same way the date filter already needs to.
# The date-based inclusion filter and the "set archive timestamp" dropdown
# are implemented entirely in ui.py/execute.py against stat() results, so
# they need no capability bit -- they work the same for every format. Very
# large selections (over BATCH_SIZE files, see ui.py) are split into
# batches and added to the archive incrementally for every format except
# shar, which has no way to build up an archive across multiple runs.
#
# The tar family (including lz/lzo/Z/lz4) is compressed via
# `tar --use-compress-program=<binary>` uniformly rather than tar's builtin
# -z/-j/-J/--zstd flags, so a faster parallel implementation (pigz, pbzip2,
# lbzip2, plzip) can be preferred over the single-threaded default when
# installed, with the same mechanism covering formats tar has no builtin
# flag for at all (lzip, lzop, compress, lz4). rzip and lrzip are
# deliberately NOT offered this way: both need random access to the whole
# file for their long-range matching, so piping them through tar's
# stdin/stdout interface defeats their purpose and forces the whole
# archive into RAM. We still detect them (see _has_rzip/_has_lrzip) in
# case a future version wants to offer them as standalone compressors.


class ArchiveFormat:
    def __init__(self, fmt_id, label, extension, capabilities=0, binary=None):
        self.id = fmt_id
        self.label = label
        self.extension = extension
        self.capabilities = capabilities
        self.bin = binary
        self.available = False
        self.compress_program = None  # tar family only: resolved --use-compress-program


def _detect_7z(formats):
    # Prefer the full "7z" build (AES-256 encryption, sfx modules, etc).
    # Fall back to the reduced "7za"/"7zr" builds some minimal installs
    # ship instead, which are only trusted to create/split/test a plain
    # archive -- their crypto/sfx support varies too much to assume.
    fmt = formats[FMT_7Z]
    if shutil.which("7z"):
        fmt.bin = "7z"
        fmt.capabilities = (CAP_ENCRYPT | CAP_SFX | CAP_RECOVERY | CAP_HEADER_ENC | CAP_SPLIT |
                             CAP_TEST | CAP_COMPRESSION | CAP_DICT_SIZE | CAP_DEDUP_REFS |
                             CAP_PRESERVE_ATIME | CAP_APPEND_EXISTING)
        fmt.available = True
    elif shutil.which("7za"):
        fmt.bin = "7za"
        fmt.capabilities = CAP_SPLIT | CAP_TEST | CAP_COMPRESSION | CAP_APPEND_EXISTING
        fmt.available = True
    elif shutil.which("7zr"):
        fmt.bin = "7zr"
        fmt.capabilities = CAP_TEST | CAP_APPEND_EXISTING
        fmt.available = True


def _detect_tar_variant(formats, fmt_id, prefs):
    """Picks the first available binary in `prefs` (preference order) as
    this tar variant's --use-compress-program. An empty `prefs` means the
    format needs no compressor (plain tar)."""
    if not shutil.which("tar"):
        return
    fmt = formats[fmt_id]
    if not prefs:
        fmt.available = True
        return
    for candidate in prefs:
        if shutil.which(candidate):
            fmt.compress_program = candidate
            fmt.available = True
            return


_cache = None
_has_rzip = False
_has_lrzip = False


def detect():
    """Returns {format_id: ArchiveFormat}, detecting installed tools once."""
    global _cache, _has_rzip, _has_lrzip
    if _cache is not None:
        return _cache

    formats = {
        FMT_7Z: ArchiveFormat(FMT_7Z, "7z", "7z"),
        FMT_ZIP: ArchiveFormat(FMT_ZIP, "zip", "zip",
                                CAP_ENCRYPT | CAP_SPLIT | CAP_TEST | CAP_TEST_INLINE |
                                CAP_COMPRESSION | CAP_COMMENT | CAP_APPEND_EXISTING, "zip"),
        FMT_TAR: ArchiveFormat(FMT_TAR, "tar", "tar", CAP_APPEND_EXISTING, "tar"),
        FMT_TAR_GZ: ArchiveFormat(FMT_TAR_GZ, "tar.gz", "tar.gz", 0, "tar"),
        FMT_TAR_BZ2: ArchiveFormat(FMT_TAR_BZ2, "tar.bz2", "tar.bz2", 0, "tar"),
        FMT_TAR_XZ: ArchiveFormat(FMT_TAR_XZ, "tar.xz", "tar.xz", 0, "tar"),
        FMT_TAR_ZST: ArchiveFormat(FMT_TAR_ZST, "tar.zst", "tar.zst", 0, "tar"),
        FMT_TAR_LZ: ArchiveFormat(FMT_TAR_LZ, "tar.lz", "tar.lz", 0, "tar"),
        FMT_TAR_LZO: ArchiveFormat(FMT_TAR_LZO, "tar.lzo", "tar.lzo", 0, "tar"),
        FMT_TAR_Z: ArchiveFormat(FMT_TAR_Z, "tar.Z", "tar.Z", 0, "tar"),
        FMT_TAR_LZ4: ArchiveFormat(FMT_TAR_LZ4, "tar.lz4", "tar.lz4", 0, "tar"),
        FMT_RAR: ArchiveFormat(FMT_RAR, "rar", "rar",
                                CAP_ENCRYPT | CAP_SFX | CAP_RECOVERY | CAP_HEADER_ENC | CAP_SPLIT |
                                CAP_TEST | CAP_COMPRESSION | CAP_DICT_SIZE | CAP_COMMENT |
                                CAP_DEDUP_REFS | CAP_STORE_MTIME | CAP_STORE_CTIME | CAP_STORE_ATIME |
                                CAP_PRESERVE_ATIME | CAP_HIGH_PRECISION_TIME | CAP_APPEND_EXISTING,
                                "rar"),
        FMT_ARJ: ArchiveFormat(FMT_ARJ, "arj", "arj",
                                CAP_ENCRYPT | CAP_SFX | CAP_FLAT_FILES_ONLY | CAP_APPEND_EXISTING, "arj"),
        FMT_ARC: ArchiveFormat(FMT_ARC, "arc", "arc",
                                CAP_FLAT_FILES_ONLY | CAP_APPEND_EXISTING, "arc"),
        FMT_LHA: ArchiveFormat(FMT_LHA, "lha", "lzh",
                                CAP_FLAT_FILES_ONLY | CAP_APPEND_EXISTING, "lha"),
        FMT_CPIO: ArchiveFormat(FMT_CPIO, "cpio", "cpio", CAP_FLAT_FILES_ONLY, "cpio"),
        FMT_SHAR: ArchiveFormat(FMT_SHAR, "shar", "shar", CAP_FLAT_FILES_ONLY, "shar"),
    }

    _detect_7z(formats)
    if shutil.which("zip"):
        formats[FMT_ZIP].available = True

    _detect_tar_variant(formats, FMT_TAR, [])
    _detect_tar_variant(formats, FMT_TAR_GZ, ["pigz", "gzip"])
    _detect_tar_variant(formats, FMT_TAR_BZ2, ["pbzip2", "lbzip2", "bzip2"])
    _detect_tar_variant(formats, FMT_TAR_XZ, ["xz"])
    _detect_tar_variant(formats, FMT_TAR_ZST, ["zstd"])
    _detect_tar_variant(formats, FMT_TAR_LZ, ["plzip", "lzip"])
    _detect_tar_variant(formats, FMT_TAR_LZO, ["lzop"])
    _detect_tar_variant(formats, FMT_TAR_Z, ["compress"])
    _detect_tar_variant(formats, FMT_TAR_LZ4, ["lz4"])

    for fmt_id, prog in ((FMT_RAR, "rar"), (FMT_ARJ, "arj"), (FMT_ARC, "arc"),
                          (FMT_LHA, "lha"), (FMT_CPIO, "cpio"), (FMT_SHAR, "shar")):
        if shutil.which(prog):
            formats[fmt_id].available = True

    _has_rzip = bool(shutil.which("rzip"))
    _has_lrzip = bool(shutil.which("lrzip"))

    _cache = formats
    return formats
