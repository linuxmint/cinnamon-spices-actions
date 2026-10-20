# Add to Archive

An "Add to Archive" right-click action for Nemo, with a tabbed dialog
modeled on WinRAR's "Add to Archive" window.

It detects which archivers are actually installed on your system and
only offers those formats in the dialog. Per-format options are enabled
or greyed out depending on what the currently selected format actually
supports; a handful of options (the date-based file filter and the
"set archive time to..." dropdown) work identically for every format
because they're implemented directly against the filesystem rather
than relying on each archiver's own, wildly inconsistent, support.

## Supported formats

| Format  | Requires                          | Encrypt | SFX | Recovery | Split | Test | Compression | Dict size | Comment | Dedup refs | Append existing |
|---------|-------------------------------------|:-------:|:---:|:--------:|:-----:|:----:|:-----------:|:---------:|:-------:|:----------:|:---------------:|
| 7z      | `7z` (or `7za`/`7zr`)               | ✓*      | ✓*  | ✓*       | ✓*    | ✓*   | ✓*          | ✓*        |         | ✓*         | ✓*              |
| zip     | `zip`                               | ✓       |     |          | ✓     | ✓    | ✓           |           | ✓       |            | ✓               |
| tar     | `tar`                               |         |     |          |       |      |             |           |         |            | ✓               |
| tar.gz  | `tar` + `gzip` (or `pigz`)          |         |     |          |       |      |             |           |         |            |                 |
| tar.bz2 | `tar` + `bzip2` (or `pbzip2`/`lbzip2`) |     |     |          |       |      |             |           |         |            |                 |
| tar.xz  | `tar` + `xz`                        |         |     |          |       |      |             |           |         |            |                 |
| tar.zst | `tar` + `zstd`                      |         |     |          |       |      |             |           |         |            |                 |
| tar.lz  | `tar` + `lzip` (or `plzip`)         |         |     |          |       |      |             |           |         |            |                 |
| tar.lzo | `tar` + `lzop`                      |         |     |          |       |      |             |           |         |            |                 |
| tar.Z   | `tar` + `compress` (`ncompress`)    |         |     |          |       |      |             |           |         |            |                 |
| tar.lz4 | `tar` + `lz4`                       |         |     |          |       |      |             |           |         |            |                 |
| rar     | `rar`                               | ✓       | ✓   | ✓        | ✓     | ✓    | ✓           | ✓         | ✓       | ✓          | ✓               |
| arj     | `arj`                               | ✓       | ✓   |          |       |      |             |           |         |            | ✓               |
| arc     | `arc`                               |         |     |          |       |      |             |           |         |            | ✓               |
| lha     | `jlha-utils` (`lha`)                |         |     |          |       |      |             |           |         |            | ✓               |
| cpio    | `cpio`                              |         |     |          |       |      |             |           |         |            |                 |
| shar    | `sharutils` (`shar`)                |         |     |          |       |      |             |           |         |            |                 |

\* Full 7z capabilities require the `7z` binary (e.g. the `p7zip-full`
package); the reduced `7za`/`7zr` builds some minimal installs ship
instead are only trusted for plain create/split/test/append.

The `tar.*` variants prefer a parallel/multi-threaded compressor (pigz,
pbzip2, lbzip2, plzip) over the plain single-threaded one when both are
installed, for faster archiving on multi-core machines; the archive
itself is byte-for-byte a normal gzip/bzip2/lzip stream either way.
`rzip`/`lrzip` are detected but deliberately not offered here: both need
random access to the whole file for their long-range matching, so piping
them through tar's stdin/stdout interface would defeat their purpose and
risk exhausting RAM on large selections.

RAR is also the only format with explicit control over which source
timestamps get stored (modification/creation/access, plus preserving
the source files' own access time) and a "high precision time" option
(RAR5's timestamps vs. RAR4's 2-second DOS-era resolution); 7z only
exposes "preserve source access time" (`-ssp`) of that set.

arj/arc/lha/cpio/shar are simple, largely-untunable formats here: we
expand every selected folder into its individual files ourselves before
handing them over (rather than trust each tool's own recursion support),
which means empty folders in your selection won't be preserved in
archives of these five formats. Everything else keeps its native
recursion (and empty-folder handling).

If none of the above are installed, the action tells you so instead of
opening an empty dialog.

## Very large selections

Selections of more than 1000 files are split into batches and added to
the archive incrementally, so there's no practical limit on how many
files you can archive at once and no risk of hitting the OS's
command-line length limit. This is transparent in the UI -- the
progress window just shows "Adding files... (batch 2 of 5)" and so on
while it works. It applies to every format capable of being added to
incrementally (everything except shar, which has no such mechanism --
selecting more than 1000 files with shar chosen shows a clear error
instead of attempting it). Compressed tar archives, which can't be
appended to directly, are built as an uncompressed temporary file one
batch at a time and compressed once at the end.

## Tabs

- **General** — archive name, format, compression method/dictionary
  size, splitting into volumes, encryption.
- **Options** — SFX, recovery record, integrity test, "save identical
  files as references" (dedup), "delete files after archiving" (asks
  for confirmation, listing how many items, before it does anything).
- **Files** — include files by date: modification/creation/access/any
  time, older/newer than a relative duration (Y/Mo/D/H/Mi/S), or
  before/after an absolute date+time. Applies per file (it walks into
  selected folders itself), the same way for every format.
- **Time** — set the resulting archive's own timestamp to the current
  system time, the archive's previous timestamp (if updating one),
  the latest timestamp among the archived files, or a specified
  date+time; plus, where supported, which source timestamps to store.
- **Comment** — an archive comment, typed in or read from a file,
  where the format supports one.

## Usage

Select one or more files or folders in Nemo, right-click, choose
**Add to Archive**, pick a format and any options, then **Create
Archive**. If the archive name you chose already exists and the format
supports it, the selected files are added to it rather than replacing
it.

The non-blocking progress window shows real, per-file progress (parsed
from the archiver's own output); a collapsed-by-default "Show files"
section lists each file as it's added, in a selectable read-only log.
**Pause** sends the archiver a real OS-level pause (`SIGSTOP`) and
becomes **Continue** to resume it (`SIGCONT`); **Work in background**
lowers its scheduling priority by one step and minimizes the window,
becoming **Run in foreground** to restore normal priority. **Work in
background** is disabled once the last file has been added to the
archive, since there's no more file-adding work left for it to affect.
On failure, the window shows the archiver's own error output.

## Notes

- shar archives are a shell script, not a binary archive format --
  `shar`'s own `-o` flag always appends `.01` to whatever name you give
  it, so this action lets it write there and then renames the result
  into place for you; you shouldn't notice the difference.
- Archive passwords are passed as a command-line argument to the
  archiver, so they're briefly visible to other local users via `ps`.
  This is an inherent limitation of driving CLI archivers rather than
  linking an archive library directly.
- Linux doesn't expose file creation time through the standard `stat()`
  the way Windows/macOS do; this action calls `statx(2)` directly to
  get a real value where the filesystem provides one (most current
  Linux filesystems do), falling back to the inode-change time
  otherwise.
- This Python/PyGObject implementation exists specifically so this
  action can be distributed as a Cinnamon Spice, which doesn't accept
  compiled languages. A separate C/GTK3 version with the same features
  also exists, for anyone who'd rather run a compiled binary standalone.

## License

GPL-2.0.
