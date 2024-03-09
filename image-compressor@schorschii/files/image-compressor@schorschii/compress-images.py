#!/usr/bin/python3

from PIL import Image
import os
import sys
import pathlib
import wx
from threading import Thread
from urllib.parse import urlparse, unquote

TARGET_WIDTH   = 1920
TARGET_QUALITY = 75

class ImageWorker(Thread):
    def __init__(self, mainFrame):
        Thread.__init__(self)
        self.frame = mainFrame
        mainFrame.Show();
        self.start()

    def run(self):
        files = []
        for arg in sys.argv:
            if(arg != sys.argv[0]):
                if(os.path.isfile(arg)):
                    files.append(arg)
                elif(arg.startswith("file://")):
                    urlPath = unquote(urlparse(arg).path)
                    if(os.path.isfile(urlPath)):
                        files.append(urlPath)

        i = 0
        n = len(files)
        sizeBefore = 0
        sizeAfter = 0
        for file in files:
            i += 1
            print("Processing " + str(i) + ": " + file)
            wx.CallAfter(self.frame.progress.SetValue, (i-1)/n*100)
            wx.CallAfter(self.frame.SetTitle, "Compressing Images " + str(i) + "/" + str(n) + "...")

            path = pathlib.Path(file)
            filename = path.stem
            fileext = path.suffix
            filepath = path.parent.absolute().as_posix()
            newFileName = filepath + "/" + filename + "_converted" + fileext

            img = Image.open(file)
            oldWidth = img.size[0]
            oldHeight = img.size[1]
            newWidth = TARGET_WIDTH
            if(oldWidth < newWidth):
                print("  Old width is smaller than target width, adjusting: newWidth = oldWidth")
                newWidth = oldWidth
            newHeight = int(oldHeight * newWidth / oldWidth)
            img = img.resize((newWidth,newHeight), Image.ANTIALIAS)
            img.save(newFileName, optimize=True, quality=TARGET_QUALITY)
            print("Saved: " + newFileName)

            sizeBefore += os.stat(file).st_size
            sizeAfter += os.stat(newFileName).st_size

        self.frame.files = n
        self.frame.sizeBefore = sizeBefore
        self.frame.sizeAfter = sizeAfter
        wx.CallAfter(self.frame.progress.SetValue, 100)
        wx.CallAfter(self.frame.SetTitle, "Compressing Images " + str(n) + "/" + str(n) + "...")
        wx.CallAfter(self.frame.Close)

class ProgressFrame(wx.Frame):
    def __init__(self):
        super(ProgressFrame, self).__init__(None, style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.InitUI()

    def InitUI(self):
        # Window Content
        panel = wx.Panel(self, wx.ID_ANY)
        self.progress = wx.Gauge(panel, wx.ID_ANY)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.progress, 1, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(sizer)

        # Window Settings
        self.SetSize(450, 65)
        self.SetTitle("Please Wait...")
        self.Centre()

    def OnClose(self, event):
        if(self.files > 0):
            dlg = wx.MessageDialog(self,
                "Files Processed: "+str(self.files)+"\n" +
                "Original Size: "+str(round(self.sizeBefore/1024))+" KiB\n" +
                "Compressed Size: "+str(round(self.sizeAfter/1024))+" KiB\n" +
                "Saving: "+str(round(100-(self.sizeAfter*100/self.sizeBefore)))+"%\n\n" +
                "Attention: compression reduced image size and quality.",
                "Image Compressing Finished",
                wx.OK
            )
            dlg.ShowModal()
        self.Destroy()


# ----------------------------------------------------------------


app = wx.App()
frame = ProgressFrame()
frame.Show()
ImageWorker(frame)
app.MainLoop()
