import io
import logging
from pathlib import Path
from typing import Optional

from azure.core.exceptions import ResourceExistsError
from azure.storage.fileshare import ShareClient, ShareFileClient

from lyra.core.cache import cache_decorator
from lyra.core.config import settings

logger = logging.getLogger(__name__)


def get_share(
    account_url=settings.AZURE_STORAGE_ACCOUNT_URL,
    share_name=settings.AZURE_STORAGE_SHARE_NAME,
    credential=settings.AZURE_STORAGE_ACCOUNT_KEY,
):

    share = ShareClient(
        account_url=account_url, share_name=share_name, credential=credential,
    )

    return share


def make_azure_fileclient(
    filepath: str, share: Optional[ShareClient] = None,
) -> ShareFileClient:  # pragma: no cover
    """Create full path to `filepath` even if it doesn't exist on the share yet.

    This iterates through the file path from bottom to top (where our file is),
    eg.: make_azure_fileclient(mnwd/database/arbitrarily/nested/test.csv)
    mnwd
    mnwd/database
    mnwd/database/arbitrarily
    mnwd/database/arbitrarily/nested
    """
    if share is None:
        share = get_share()  # get default share

    filepath = Path(filepath)
    parents = list(filepath.parents)[:-1]  # don't need root '.'
    for i, child in enumerate(reversed(parents)):
        try:
            _ = share.create_directory(str(child))
        except ResourceExistsError:
            pass

    client = share.get_file_client(str(filepath))

    return client


def get_file_object(filepath, share=None):
    file_client = make_azure_fileclient(filepath, share=share)
    logger.info(f"retrieving {filepath} from azure...")
    data = file_client.download_file()
    file = io.BytesIO()
    data.readinto(file)
    file.seek(0)
    return file


def put_file_object(fileobj_src, filepath_dest, share=None):  # pragma: no cover
    fileobj_src.seek(0)
    file_client = make_azure_fileclient(filepath_dest, share=share)
    logger.info(f"uploading {filepath_dest} to azure...")
    file_client.upload_file(fileobj_src)
    logger.info("upload completed")
    return


@cache_decorator(ex=None)  # expires only when cache is flushed.
def get_file_as_bytestring(filepath, share=None):
    file = get_file_object(filepath, share=share)
    return file.read()
