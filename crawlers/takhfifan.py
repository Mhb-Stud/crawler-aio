from bs4 import BeautifulSoup
import asyncio
import aiohttp
from datetime import date, timedelta
from publisher import Publisher


class TakhfifanCoupon:
    name = 'takhfifan'

    start_urls = ['https://takhfifan.com/v4/api/rainman/vendors?limit=1000']

    @classmethod
    def get_vendor_coupons(cls, response, session):
        vendor_coupons = []
        for vendor in response['data']:
            vendor_coupons.append(session.get(
                f'https://takhfifan.com/v4/api/rainman/vendors/{vendor["attributes"]["slug"]}/offers?limit=1000&filter_by=coupon,cashpon', 
                ssl=False))
        return vendor_coupons


    @classmethod
    async def create_coupon_data(cls, offer, session):
        response = await session.get(f'https://takhfifan.com/v4/api/rainman/offers/{offer["id"]}/coupons/invalidate')
        response = await response.json()
        offer['attributes']['code'] = response['data']['attributes']['code']
        offer = offer['attributes']
        return offer

    @classmethod
    async def get_coupons(cls, response, session):
        offers = []
        for vendor in response:
            vendor_offers = await vendor.json()
            vendor_offers = vendor_offers['data']
            for offer in vendor_offers:
                offers.append(cls.create_coupon_data(offer=offer, session=session))
        coupons = await asyncio.gather(*offers)
        return coupons
                    

    @classmethod
    def parse_coupon_detailed(cls, response, publisher):
        offer = response
        if offer['expires_at']:
            coupon = {
                'source': cls.name,
                'title': offer['title'],
                'description': BeautifulSoup(offer['description'], features='lxml').text,
                'vendor': offer['vendor']['name'],
                'expires_at': offer['expires_at'],
                'percentage': offer['percentage'],
                'amount': offer['amount'],
                'ceiling': offer['ceiling'],
                'code': offer['code'],
            }
            publisher.process_item(item=coupon)

    @classmethod
    async def main(cls):
        async with aiohttp.ClientSession() as session:
            start_url = 'https://takhfifan.com/v4/api/rainman/vendors?limit=1000'
            first_page = await session.get(start_url, ssl=False)
            response = await first_page.json()
            vendor_coupons = await asyncio.gather(*cls.get_vendor_coupons(response=response, session=session))
            publisher = Publisher()
            # for vendor in vendor_coupons:
            #     coupon_details = await cls.get_coupons(response=vendor, session=session)
            coupon_details = await cls.get_coupons(response=vendor_coupons, session=session)
            for coupon_detail in coupon_details:
                cls.parse_coupon_detailed(response=coupon_detail, publisher=publisher)


if __name__ == '__main__':
    asyncio.run(TakhfifanCoupon.main())


