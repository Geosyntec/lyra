import ftplib
import io
from pathlib import Path

import pandas

from lyra.core.config import settings

def get_file_object_from_MNWDShareFile(conn, filename_src):
    file = io.BytesIO()
    conn.retrbinary('RETR '+ filename_src, file.write)
    return file

    # if filepath_dest is None:
    #     filepath_dest = Path(filename_src).name

    # with open(filepath_dest, 'wb') as f:
    #     file.seek(0)
    #     f.write(file.read())
    #     file.close()
    #     del file
    # return filepath_dest

def write_file(file_obj, filepath_dest):

    with open(filepath_dest, 'wb') as f:
        file.seek(0)
        f.write(file.read())
        file.close()
        del file
    # return filepath_dest
