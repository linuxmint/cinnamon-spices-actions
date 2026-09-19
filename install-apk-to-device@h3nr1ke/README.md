INSTALL APK TO DEVICE
=====================

Install the selected `.apk` file to the indicated device or emulator

DESCRIPTION
-----------

By selecting the `.apk`, a list of the available devices and emulators will be
displayed to indicate where the file will be installed.

It is important to highlight that this action dependend on the softwares `adb` and `emulator` that are available once you install the [Android Studio](https://developer.android.com/studio) or you should install the [Command Line Only option](https://developer.android.com/studio/index.html#command-line-tools-only).

for example

``` bash
# add adb and emulator to the path so the action will be able to use them

sudo ln -s /home/youruser/Android/Sdk/platform-tools/adb /usr/bin/adb
sudo ln -s /home/youruser/Android/Sdk/emulator/emulator /usr/bin/emulator
```

DEPENDENCIES
------------

The following programs must be installed and available:

* `gettext` to get the correct translation to the action
* `bash` to execute the commands
* `adb` the adb sotware must be in the PATH variable
* `emulator` the emualtor must be in the PATH variable
