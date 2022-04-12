import os
import shutil
import time
import zipfile
import PyInstaller.__main__

if __name__ == "__main__":

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

    zipf = zipfile.ZipFile("blessmodder.zip", "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk("blessmodder"):
        for file in files:
            zipf.write(os.path.join(root, file))

    zipf.close()