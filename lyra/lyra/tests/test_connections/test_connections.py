import pytest

from lyra.connections import azure_fs, database, ftp


@pytest.mark.integration
def test_connected_database_engine():
    engine = database.database_engine()
    database.reconnect_engine(engine)
    assert len(engine.table_names()) > 1


@pytest.mark.integration
def test_azure_share():
    share = azure_fs.get_share()
    assert share is not None


@pytest.mark.integration
def test_mnwd_ftp():
    with ftp.mnwd_ftp() as conn:
        files = conn.nlst()
    assert len(files) > 0


@pytest.mark.integration
def test_azure_get_file_as_bytestring(nocache):
    file = azure_fs.get_file_as_bytestring(
        "mnwd/drooltool/spatial/rsb_geo_data_latest.csv", share=None
    )

    assert len(file) > 50
    assert b"CatchIDN,DwnCatchIDN,Watershed" in file[:100]
