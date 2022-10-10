import shutil
import os
import zipfile
import tarfile
import py7zr
import gzip


def is_gzipfile(path: str):
    with open(path, "rb") as f:
        return f.read(2) == b"\x1f\x8b"


def is_compressed(path: str):
    if os.path.isdir(path):
        return False

    return (
        zipfile.is_zipfile(path)
        or tarfile.is_tarfile(path)
        or py7zr.is_7zfile(path)
        or is_gzipfile(path)
    )


def decompress(path: str):
    temp = path + "_temp"
    try:
        if zipfile.is_zipfile(path):
            os.makedirs(temp)
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(temp)
            arctype = "zip"
        elif tarfile.is_tarfile(path):
            if path.endswith("gz"):
                tartype = ":gz"
            elif path.endswith("bz") or path.endswith("bz2"):
                tartype = ":bz2"
            elif path.endswith("xz"):
                tartype = ":xz"
            elif path.endswith("lzma"):
                tartype = ":lzma"
            else:
                tartype = ""
            with tarfile.open(path, "r" + tartype) as tf:
                tf.extractall(temp)
            arctype = "tar" + tartype
        elif py7zr.is_7zfile(path):
            with py7zr.SevenZipFile(path, "r") as zf:
                zf.extractall(temp)
            arctype = "7zip"
        elif is_gzipfile(path):
            with gzip.open(path, "rb") as gzf:
                with open(temp, "wb") as f:
                    f.write(gzf.read())
            arctype = "gzip"
        else:
            return
        os.remove(path)
        os.rename(temp, path)
        return arctype
    except Exception:
        try:
            if os.path.isdir(temp):
                shutil.rmtree(temp)
            else:
                os.remove(temp)
        except FileNotFoundError:
            pass


def compress(path: str, arctype: str):
    temp = path + "_temp"
    if arctype == "zip":
        with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    p = os.path.join(root, filename)
                    zf.write(p, arcname=p.replace(path, "").lstrip(os.path.sep))

    elif arctype.startswith("tar"):
        tartype = arctype.replace("tar", "")
        with tarfile.open(temp, "w" + tartype) as tf:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    p = os.path.join(root, filename)
                    tf.add(p, arcname=p.replace(path, "").lstrip(os.path.sep))

    elif arctype == "7zip":
        with py7zr.SevenZipFile(temp, "w") as zf:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    p = os.path.join(root, filename)
                    zf.write(p, arcname=p.replace(path, "").lstrip(os.path.sep))

    elif arctype == "gzip":
        with open(path, "rb") as f:
            with gzip.open(temp, "wb") as gzf:
                gzf.write(f.read())

    else:
        return

    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except FileNotFoundError:
        pass
    os.rename(temp, path)
