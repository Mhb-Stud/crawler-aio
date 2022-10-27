import asyncio
import aiohttp
import json
from datetime import date, timedelta
from publisher import Publisher


async def offch():
    async with aiohttp.ClientSession() as session:
        start_url = 'https://api.offch.com/api/coupons?category=1&limit=984654'
        fp = await session.get(start_url, ssl=False)
        response = await fp.json()
        publisher = Publisher()
        for coupon in response['results']:
            if coupon['code'] is not None:
                expiration_date = coupon['expire_datetime']
                if expiration_date is None and coupon['is_expired'] is False:
                    now = date.today()
                    expiration_date = str(now + timedelta(days=2)) + "T00:00:00"
                if expiration_date:
                    coupon =  {
                        'source': 'offch',
                        'title': coupon['title'],
                        'description': coupon['description'],
                        'vendor': coupon['shop']['name'],
                        'expires_at': expiration_date,
                        'percentage': coupon['percent'],
                        'amount': coupon['value'],
                        'ceiling': coupon['max_value'],
                        'code': coupon['code'][0],
                        'min_order': coupon['min_order']
                    }
                    publisher.process_item(item=coupon)


if __name__ == '__main__':
    asyncio.run(offch())

