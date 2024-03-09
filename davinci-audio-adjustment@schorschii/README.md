DAVINCI RESOLVE AUDIO ADJUSTMENT
================================

Converts the audio track of a video file for usage with DaVinci Resolve Studio.

DESCRIPTION
-----------

DaVinci Resolve Studio unfortunately does not support AAC audio (often found in consumer camera videos). This action converts the AAC audio track of a video file to PCM while letting the video quality untouched.

DEPENDENCIES
------------

The following packages must be installed:

* `ffmpeg` for audio conversion
* `zenity` to display the dialog with the result
