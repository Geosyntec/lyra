import ftplib
import io

from lyra.core.config import settings


def ftp(location, username, password, directory=""):
    """open a connection to MNWD's ftp site and manage login

    Returns:
    --------
    conn : open ftp connection object ready to retrieve files.
    Usage:

    import io
    from lyra.connections.ftp import ftp

    with ftp() as ftp:
        file = io.BytesIO()
        ftp.retrbinary("RETR "+ "filename_src", file.write)

    """
    conn = ftplib.FTP(location)
    conn.login(username, password)
    conn.cwd(directory)
    return conn


def mnwd_ftp():
    conn = ftp(
        location=settings.MNWD_FTP_LOCATION,
        username=settings.MNWD_FTP_USERNAME,
        password=settings.MNWD_FTP_PASSWORD,
        directory=settings.MNWD_FTP_DIRECTORY,
    )
    return conn


def get_file_object(ftp: ftplib.FTP, filename: str) -> io.BytesIO:
    """returns the filename as an open bytes file object"""
    file = io.BytesIO()
    ftp.retrbinary("RETR " + filename, file.write)
    file.seek(0)

    return file


def get_latest_file_from_list(file_list: list, slug=None) -> str:
    if slug is None:
        slug = ""
    return sorted(filter(lambda x: slug in x.lower(), file_list)).pop()


def get_latest_filename_from_ftp(ftp: ftplib.FTP, slug=None) -> str:
    return get_latest_file_from_list(ftp.nlst(), slug)


def get_latest_file_as_object(ftp: ftplib.FTP, fileslug: str) -> io.BytesIO:

    latest = get_latest_filename_from_ftp(ftp, fileslug)
    file = get_file_object(ftp, latest)
    file.ftp_name = latest
    print(__file__, file.ftp_name)

    return file
