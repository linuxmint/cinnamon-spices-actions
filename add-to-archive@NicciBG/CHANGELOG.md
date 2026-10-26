# Changelog

## 1.0
Initial release: a WinRAR-style "Add to Archive" dialog for Nemo.

- Supports 17 formats -- 7z, zip, tar, tar.gz, tar.bz2, tar.xz, tar.zst,
  tar.lz, tar.lzo, tar.Z, tar.lz4, rar, arj, arc, lha, cpio, shar --
  offering only the formats whose underlying tool is actually
  installed, and greying out per-format options (encryption, SFX,
  recovery record, splitting, post-creation testing, etc.) that the
  selected format doesn't support. Every `tar.*` variant prefers a
  parallel compressor (pigz, pbzip2, lbzip2, plzip) over the
  single-threaded default when both are installed, for faster
  archiving on multi-core machines.
- Adding to an archive that already exists updates it in place for
  7z/zip/rar/plain tar/arj/arc/lha (compressed tar.* archives can't be
  updated in place, so that combination is refused with an explanation
  instead of silently overwriting).
- **General** tab: archive name/format, compression method
  (store/fastest/fast/normal/good/best) and dictionary size where the
  format supports them, splitting into volumes, and encryption
  (including file-name encryption).
- **Options** tab: self-extracting archive (SFX), recovery record,
  integrity test after creation, "save identical files as references"
  (dedup), and "delete files after archiving" (guarded by its own
  confirmation dialog listing how many items).
- **Files** tab: include files by date (modification/creation/access/
  any time; older/newer than a relative duration, or before/after an
  absolute date+time). Applies per file the same way for every format,
  independent of each archiver's own (inconsistent) support.
  Creation-time filtering uses the real filesystem birth time (via
  `statx`) where the filesystem exposes one, not just mtime/ctime.
- **Time** tab: set the resulting archive's own timestamp (current
  system time / original archive time / latest file time / a specified
  date+time), plus, where the format supports it, explicit control
  over which source timestamps get stored and a high-precision time
  option.
- **Comment** tab: embed a text or file-sourced archive comment, where
  the format supports one.
- Selections larger than 1000 files are split into batches and added
  to the archive incrementally instead of being handed to the archiver
  in one command, for every format that can be built up incrementally
  (all of them except shar, which shows a clear error instead if asked
  to handle more than 1000 files). Compressed tar archives are built
  as an uncompressed temp file one batch at a time and compressed once
  at the end, since they can't be appended to directly.
- The progress window shows real, per-file progress (parsed from each
  archiver's own output), a collapsed-by-default "Show files" section
  listing each file as it's added, a **Pause**/**Continue** button
  (sends `SIGSTOP`/`SIGCONT` to the running archiver -- a real
  OS-level pause that needs no cooperation from the archiver itself),
  and a **Work in background** button that lowers the archiver's
  scheduling priority by one nice step and minimizes the window,
  becoming **Run in foreground** to restore normal priority; it's
  disabled once the last file has been added to the archive, since
  there's no more file-adding work left for it to affect.
