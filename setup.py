import os
import shutil
import time
import zipfile
import PyInstaller.__main__
import re

if __name__ == "__main__":

    ver = None
    with open("blessmodder.py", "r") as f:
        for line in f:
            m = re.match('ver = "(.*)"', line)
            if m is not None:
                ver = m.groups()[0]
                print(f"Found version: {ver}")
                break

    if os.path.isdir("build"):
        shutil.rmtree("build")
    if os.path.isdir("dist"):
        shutil.rmtree("dist")
    if os.path.isdir("blessmodder"):
        shutil.rmtree("blessmodder")
    PyInstaller.__main__.run(["blessmodder.py", "--onefile"])
    os.rename("dist", "blessmodder")
    shutil.copy("LICENSE", "blessmodder/LICENSE")
    shutil.copy("readme.md", "blessmodder/readme.md")

    zipf = zipfile.ZipFile(f"blessmodder-{ver}.zip", "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk("blessmodder"):
        for file in files:
            zipf.write(os.path.join(root, file))

    zipf.close()