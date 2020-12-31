import asyncio

import numpy as np
import pytest

from jina.flow.asyncio import AsyncFlow
from jina.logging.profile import TimeContext


def validate(req):
    assert len(req.docs) == 5
    assert req.docs[0].blob.ndim == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('rest_api', [False, True])
async def test_run_async_flow(rest_api):
    with AsyncFlow(rest_api=rest_api).add() as f:
        await f.index_ndarray(np.random.random([5, 4]), on_done=validate)


async def run_async_flow_5s(rest_api):
    # WaitDriver pause 5s makes total roundtrip ~5s
    with AsyncFlow(rest_api=rest_api).add(uses='- !WaitDriver {}') as f:
        await f.index_ndarray(np.random.random([5, 4]), on_done=validate)


async def sleep_print():
    # total roundtrip takes ~5s
    print('heavylifting other io-bound jobs, e.g. download, upload, file io')
    await asyncio.sleep(5)
    print('heavylifting done after 5s')


async def concurrent_main(rest_api):
    # about 5s; but some dispatch cost, can't be just 5s, usually at <7s
    await asyncio.gather(run_async_flow_5s(rest_api), sleep_print())


async def sequential_main(rest_api):
    # about 10s; with some dispatch cost , usually at <12s
    await run_async_flow_5s(rest_api)
    await sleep_print()


@pytest.mark.asyncio
@pytest.mark.parametrize('rest_api', [False, True])
async def test_run_async_flow_other_task_sequential(rest_api):
    with TimeContext('sequential await') as t:
        await sequential_main(rest_api)

    assert t.duration >= 10


@pytest.mark.asyncio
@pytest.mark.parametrize('rest_api', [False, True])
async def test_run_async_flow_other_task_concurrent(rest_api):
    with TimeContext('concurrent await') as t:
        await concurrent_main(rest_api)

    # some dispatch cost, can't be just 5s, usually at <7s
    assert t.duration < 8