import asyncio
import aiohttp
import json
from datetime import date, timedelta
from publisher import Publisher

def get_tasks(session, current_page_url, total_pages):
    tasks = []
    next_page_url = current_page_url
    for i in range(total_pages):
        next_page_url = get_next_page_url(current_page=next_page_url)
        tasks.append(session.get(next_page_url, ssl=False))
    return tasks

def get_coupon_requests(session, coupons):
    tasks = []
    for coupon in coupons:
        tasks.append(session.get(f'http://www.application.mopon.ir/api/coupon/find/{coupon["id"]}', ssl=False))
    return tasks


def get_next_page_url(current_page, increment = 1):
    page_number = get_page_number(page_url=current_page)
    return current_page.replace(page_number, str(int(page_number) + increment))

def get_page_number(page_url):
    return page_url.split('=')[-1]

def process_coupon(response, publisher):
    coupon_details = response['data']
    # avoids sending coupons with null code
    if coupon_details['code']:
        vendor = coupon_details['name']
        expiration_date = str(coupon_details['expiration_date'])
        if expiration_date is None and coupon_details['is_expired'] == 0:
            now = date.today()
            expiration_date = str(now + timedelta(days=2)) + "T00:00:00"

        if expiration_date:
            coupon = {
                'source': 'mopon',
                'title': coupon_details['title'].replace("\u200c", ""),
                'description': coupon_details['content'].replace("\u200c", ""),
                'vendor': vendor,
                'expires_at': expiration_date,
                'code': coupon_details['code'],
            }
            publisher.process_item(item=coupon)

async def mopon():
    async with aiohttp.ClientSession() as session:
        start_url = 'http://www.application.mopon.ir/api/coupon/get?category_id=JBGDg&order_by=newest&page=0'
        fp = await session.get('http://www.application.mopon.ir/api/coupon/get?category_id=JBGDg&order_by=newest&page=1', ssl=False)
        last_page_url = ( await fp.json()).get('data').get('last_page_url', None)
        if last_page_url:
            last_page = int(get_page_number(last_page_url))
            responses = await asyncio.gather(*get_tasks(session=session, current_page_url=start_url, total_pages=last_page))
            publisher = Publisher()
            for r in responses:
                coupon_list = await r.json()
                coupon_list = coupon_list['data']['data']
                coupons = await asyncio.gather(*get_coupon_requests(session=session, coupons=coupon_list))
                for coupon in coupons:
                    res = await coupon.json()
                    process_coupon(response=res, publisher=publisher)


if __name__ == '__main__':
    asyncio.run(mopon())

