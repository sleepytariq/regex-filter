import shutil
import os
import zipfile
import tarfile
import py7zr
import gzip
import bz2
import lzma


def is_gzipfile(path: str):
    with open(path, "rb") as f:
        return f.read(2) == b"\x1f\x8b"


def is_bzip2file(path: str):
    with open(path, "rb") as f:
        return f.read(3) == b"\x42\x5a\x68"


def is_lzmafile(path: str):
    with open(path, "rb") as f:
        return f.read(5) == b"\xfd\x37\x7a\x58\x5a"


def is_compressed(path: str):
    if os.path.isdir(path):
        return False

    return (
        zipfile.is_zipfile(path)
        or tarfile.is_tarfile(path)
        or py7zr.is_7zfile(path)
        or is_gzipfile(path)
        or is_bzip2file(path)
        or is_lzmafile(path)
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

        elif is_bzip2file(path):
            with bz2.open(path, "rb") as bzf:
                with open(temp, "wb") as f:
                    f.write(bzf.read())
            arctype = "bzip2"

        elif is_lzmafile(path):
            with lzma.open(path, "rb") as lf:
                with open(temp, "wb") as f:
                    f.write(lf.read())
            arctype = "lzma"

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

    elif arctype == "bzip2":
        with open(path, "rb") as f:
            with bz2.open(temp, "wb") as bzf:
                bzf.write(f.read())

    elif arctype == "lzma":
        with open(path, "rb") as f:
            with lzma.open(temp, "wb") as lf:
                lf.write(f.read())

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
