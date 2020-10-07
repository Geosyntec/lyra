from typing import Optional

from lyra.core.cache import cache_decorator
from lyra.src.rsb.graph import rsb_downstream_trace, rsb_upstream_trace


@cache_decorator(ex=3600, as_response=True)  # expires in 6 hours
def rsb_upstream_trace_response(
    catchidn: int,
    geojson_file: Optional[str] = None,
    share: Optional[str] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
) -> bytes:
    result: bytes = rsb_upstream_trace(
        catchidn=catchidn,
        geojson_file=geojson_file,
        share=share,
        source=source,
        target=target,
    )
    return result


@cache_decorator(ex=3600, as_response=True)  # expires in 6 hours
def rsb_downstream_trace_response(
    catchidn: int,
    geojson_file: Optional[str] = None,
    share: Optional[str] = None,
    source: Optional[str] = None,
    target: Optional[str] = None,
) -> bytes:
    result: bytes = rsb_downstream_trace(
        catchidn=catchidn,
        geojson_file=geojson_file,
        share=share,
        source=source,
        target=target,
    )
    return result
