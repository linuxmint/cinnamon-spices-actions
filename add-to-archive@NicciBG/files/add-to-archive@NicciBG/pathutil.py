"""Common-parent-directory and relative-path math, shared by ui.py.

Keeps archived entries relative to a common parent instead of embedding
absolute paths, and avoids treating e.g. /home/user as a parent of
/home/user2 (a real bug in the original prototype's naive prefix match).

Also has the file-timestamp helpers behind the "Files" (date filter) and
"Time" tabs: standard os.stat() doesn't expose file creation/birth time
on Linux at all, so get_file_times() calls the statx(2) syscall directly
via ctypes (verified against both a hand-written C statx caller and GNU
coreutils' own `stat` output -- see the project README).
"""

import ctypes
import os


def common_parent_dir(files):
    if not files:
        return "."

    parent = os.path.dirname(files[0])

    for candidate in files[1:]:
        while True:
            plen = len(parent)
            under = candidate.startswith(parent) and (
                plen == 0 or (len(candidate) > plen and candidate[plen] == "/")
            )
            if under:
                break
            if parent in ("/", "", "."):
                parent = "/"
                break
            parent = os.path.dirname(parent)

    return parent


def relative_to(file, parent):
    if file == parent:
        return "."
    if file.startswith(parent) and len(file) > len(parent) and file[len(parent)] == "/":
        return file[len(parent) + 1:]
    return file


def strip_last_extension(name):
    root, ext = os.path.splitext(name)
    return root if root and ext else name


def expand_files_recursive(files):
    """Recursively expands `files` (which may include directories) into a
    flat list of regular files/symlinks, for callers (the date filter)
    that need to test every individual file rather than letting the
    archiver recurse into directories itself."""
    out = []

    def walk(path):
        if os.path.isdir(path) and not os.path.islink(path):
            try:
                names = os.listdir(path)
            except OSError:
                return
            for name in names:
                walk(os.path.join(path, name))
        else:
            out.append(path)

    for f in files:
        walk(f)
    return out


class _StatxTimestamp(ctypes.Structure):
    _fields_ = [
        ("tv_sec", ctypes.c_int64),
        ("tv_nsec", ctypes.c_uint32),
        ("__reserved", ctypes.c_int32),
    ]


class _Statx(ctypes.Structure):
    _fields_ = [
        ("stx_mask", ctypes.c_uint32),
        ("stx_blksize", ctypes.c_uint32),
        ("stx_attributes", ctypes.c_uint64),
        ("stx_nlink", ctypes.c_uint32),
        ("stx_uid", ctypes.c_uint32),
        ("stx_gid", ctypes.c_uint32),
        ("stx_mode", ctypes.c_uint16),
        ("__spare0", ctypes.c_uint16 * 1),
        ("stx_ino", ctypes.c_uint64),
        ("stx_size", ctypes.c_uint64),
        ("stx_blocks", ctypes.c_uint64),
        ("stx_attributes_mask", ctypes.c_uint64),
        ("stx_atime", _StatxTimestamp),
        ("stx_btime", _StatxTimestamp),
        ("stx_ctime", _StatxTimestamp),
        ("stx_mtime", _StatxTimestamp),
        ("stx_rdev_major", ctypes.c_uint32),
        ("stx_rdev_minor", ctypes.c_uint32),
        ("stx_dev_major", ctypes.c_uint32),
        ("stx_dev_minor", ctypes.c_uint32),
        ("stx_mnt_id", ctypes.c_uint64),
        ("stx_dio_mem_align", ctypes.c_uint32),
        ("stx_dio_offset_align", ctypes.c_uint32),
        ("__spare3", ctypes.c_uint64 * 12),
    ]


_AT_FDCWD = -100
_STATX_BTIME = 0x800
_STATX_ALL = 0xFFF
_libc = ctypes.CDLL(None, use_errno=True)


def get_file_times(path):
    """Returns (mtime, ctime, atime, btime, has_btime) as Unix epoch
    seconds with fractional precision, or None if the path can't be
    stat()'d. btime falls back to ctime (with has_btime=False) on
    filesystems that don't expose a real creation time."""
    buf = _Statx()
    ret = _libc.statx(_AT_FDCWD, os.fsencode(path), 0, _STATX_ALL, ctypes.byref(buf))
    if ret != 0:
        return None

    mtime = buf.stx_mtime.tv_sec + buf.stx_mtime.tv_nsec / 1e9
    ctime = buf.stx_ctime.tv_sec + buf.stx_ctime.tv_nsec / 1e9
    atime = buf.stx_atime.tv_sec + buf.stx_atime.tv_nsec / 1e9

    if buf.stx_mask & _STATX_BTIME:
        btime = buf.stx_btime.tv_sec + buf.stx_btime.tv_nsec / 1e9
        has_btime = True
    else:
        btime = ctime
        has_btime = False

    return (mtime, ctime, atime, btime, has_btime)


# Date filter fields/conditions (values shared with the combo box ids in ui.py).
TIME_FIELD_MODIFICATION = "0"
TIME_FIELD_CREATION = "1"
TIME_FIELD_ACCESS = "2"
TIME_FIELD_ANY = "3"

DATE_COND_OLDER = "older"   # threshold = a duration in seconds
DATE_COND_NEWER = "newer"   # threshold = a duration in seconds
DATE_COND_BEFORE = "before"  # threshold = an absolute Unix timestamp
DATE_COND_AFTER = "after"    # threshold = an absolute Unix timestamp


def _time_matches(file_time, cond, threshold, now):
    if cond == DATE_COND_OLDER:
        return (now - file_time) >= threshold
    if cond == DATE_COND_NEWER:
        return (now - file_time) <= threshold
    if cond == DATE_COND_BEFORE:
        return file_time < threshold
    if cond == DATE_COND_AFTER:
        return file_time > threshold
    return True


def file_matches_date_filter(path, field, cond, threshold, now):
    """Returns True if `path` should be included under the given date
    filter. For OLDER/NEWER, `threshold` is a duration in seconds
    measured back from `now`; for BEFORE/AFTER it's an absolute Unix
    timestamp. TIME_FIELD_ANY matches if mtime, btime or atime does."""
    times = get_file_times(path)
    if times is None:
        return True  # can't stat it -- don't silently drop it from the archive
    mtime, _ctime, atime, btime, _has_btime = times

    if field == TIME_FIELD_MODIFICATION:
        return _time_matches(mtime, cond, threshold, now)
    if field == TIME_FIELD_CREATION:
        return _time_matches(btime, cond, threshold, now)
    if field == TIME_FIELD_ACCESS:
        return _time_matches(atime, cond, threshold, now)
    if field == TIME_FIELD_ANY:
        return (_time_matches(mtime, cond, threshold, now) or
                _time_matches(btime, cond, threshold, now) or
                _time_matches(atime, cond, threshold, now))
    return True
