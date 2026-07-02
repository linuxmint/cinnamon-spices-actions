# Nemo-Action-Change-files-modification-date

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Mint-informational)
![Author](https://img.shields.io/badge/made%20with-%E2%9D%A4%EF%B8%8F%20by%20FranzBias-blueviolet)

### Nemo-Action: Changing the Modification Date of Selected Files

Hello everyone, this is my first project on **GitHub**... I spent an entire night on it! Mostly to create the .sh code, and partly just to understand how GitHub works xD.

## ✨ What Is It About?

This is an **Action** for the file manager **[Nemo](https://https://github.com/linuxmint/nemo)** to change with a right-click **the modification date of one or more files** selected with the mouse. I also wanted to be able to change the creation date, but after a hundred failed attempts, I gave up. I would be infinitely grateful if someone could help me with that!

The Action is **multilingual**, currently only in 🇮🇹 **Italian**, 🇩🇪 **German**, 🇬🇧 **English**, 🇫🇷 **French**, 🇪🇸 **Spanish** and 🇵🇹 **Portuguese**.

If someone could **test it** in these languages, I would be very happy. Also, **if someone suggests other languages**, I will implement them in the action.

## ⚡️ Which Files Make Up the Action?

This Action is composed of two files:

* the file `Change-files-modification-date.nemo_action` which is the file read by Nemo to execute the Action and which contains the instructions to load the second file (as well as setting the name and the icon that will be displayed when you right-click an icon, and other little things – I’ll talk about it later);
* the file `Change-files-modification-date.sh` which contains the actual bash script that will help you modify the date of the files you have selected.

## 🛠️ Action Dependencies

To run the script correctly, a few dependencies are required:

* `zenity` - For dialog windows.  
  If you haven’t installed it yet you can do so with: `sudo apt install zenity`;
* `coreutils` - Contains touch to modify the date.  
  If you haven’t installed it yet you can do so with: `sudo apt install coreutils`

## 🧪 Procedure:

These two files, for the Action to work, must be placed **<ins>both</ins>** in the folder `.local/share/nemo/actions` (as with all Nemo actions).  
Then you need to open this folder in your terminal – usually, when you are in that folder in Nemo, right-clicking on an empty area and choosing `Apri nel terminale`, or by opening the terminal (CTRL+ALT+T) and issuing the command `cd $HOME/.local/share/nemo/actions` – and make the file `Change-files-modification-date.sh` executable by issuing the command `chmod +x Change-files-modification-date.sh`.

Once this is done, you need to:

1. **Close Nemo**: either by closing it normally from the window of our beloved file manager (making sure you have closed any other open Nemo windows), or from the Terminal by issuing the command `nemo -q`.
2. **Reopen Nemo**: either in the usual way (I won’t explain how, I’m sure you know it well!), or by issuing the command `nemo` in your Terminal.

## 🚀 Ready, Set, GO!

From now on, when you select one or more files in Nemo, by right-clicking on them, you will see a new menu item: `Modifica la data`.

![](assets/Menu.png)

Clicking on it will start the actual process contained in the `.sh` file to change the modification date of the selected file(s).

At first, you will be asked whether or not to create a **backup** of the files that will be modified (the backup will have the extension `.bkp`) and whether to create a **Debug**. Both, if chosen, will be created in the same folder where the files you chose to modify are located.

Then a calendar dialog window (`zenity --calendar`) will open where you can select the new date, as you wish. You can change the day, the month, and the year directly from there.

![](assets/Calendario.png)

Once you click OK, a new dialog window will appear – a dropdown menu – in which you can select the time; for convenience, it is set in 30-minute increments (00:00 - 23:30).

![](assets/Orario.png)

Click OK here as well and the final confirmation window will appear...

![](assets/Completato.png)

...and the modification date of the selected file(s) will be, like magic, changed.

Easy, right?

---

## 📄 License

MIT – do whatever you want, just don't remove my name 😉

## ✍️ Author

Made with ❤️ by Franz Bias (Francesco)  [![GitHub stars](https://img.shields.io/github/stars/FranzBias/Nemo-Action-Change-files-modification-date?style=social)](https://github.com/FranzBias/Nemo-Action-Change-files-modification-date/stargazers)<BR>
[https://www.bybias.com](https://www.bybias.com)

## 🤝 Contribute

Contributions are welcome!  
If you have suggestions, improvements, or bug reports, feel free to:

- Fork this repository
- Make your changes
- Open a pull request

---
