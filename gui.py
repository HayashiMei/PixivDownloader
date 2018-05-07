from tkinter import *
from tkinter.filedialog import askdirectory
import pixiv


def selectPath():
    path_ = askdirectory()
    path.set(path_)


def download():
    p = pixiv.Pixiv(save_path=path.get(), artistId=pixivId.get())
    p.start()


root = Tk()
root.title('Pixiv Downloader')

frameA = Frame()
frameA.grid(row=0, column=0)

Label(frameA, text="目标路径:").grid(row=0, column=0)
path = StringVar()
entryPath = Entry(frameA, textvariable=path)
entryPath.grid(row=0, column=1)
entryPath['state'] = 'readonly'
Button(frameA, text="路径选择", command=selectPath).grid(row=0, column=2)

Label(frameA, text="Pixiv ID:").grid(row=1, column=0)
pixivId = StringVar()
entryPixivId = Entry(frameA, textvariable=pixivId)
entryPixivId.grid(row=1, column=1, columnspan=2, sticky=E + W)
entryPixivId['state'] = 'normal'

frameC = Frame()
frameC.grid(row=1, column=0)

btnSubmit = Button(frameC, text="Download", command=download)
btnSubmit.grid(row=0)

root.mainloop()