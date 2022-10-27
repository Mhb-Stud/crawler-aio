import asyncio
from crawlers.mopon import mopon
from crawlers.takhfifan import TakhfifanCoupon
from crawlers.offch import offch
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

crawlers = {}

async def start_all():

    crawlers['mopon'] = asyncio.create_task(mopon())
    crawlers['takhfifan'] = asyncio.create_task(TakhfifanCoupon.main())
    crawlers['offch'] = asyncio.create_task(offch())
    try:
        for vendor, task in crawlers.items():
            await task
    except asyncio.CancelledError:
        print(f'{vendor} was stopped')
        crawlers.clear()


@app.get("/startall")
async def root(background_tasks: BackgroundTasks):

    background_tasks.add_task(start_all)
    return {'status': 'success',
            'message': 'all coupon crawlers were started'
            }

@app.get("/stopall")
async def root():
    for vendor, task in crawlers.items():
        task.cancel()
    crawlers.clear()
    return {'status': 'success',
            'message': 'all coupon crawlers were stopped'
            }

@app.get("/running")
async def root():
    spiders = []
    for vendor, task in crawlers.items():
        spiders.append(vendor)
    return {'status': 'success',
            'message': spiders
            }


def main():
    asyncio.run(start_all())

if __name__ == '__main__':
    main()