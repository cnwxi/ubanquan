import hashlib
import json
import random
from time import sleep, perf_counter
from urllib.parse import quote
import requests
import cart
import threading


class ubanquan:
    def __init__(self):
        with open("./config.json", "r",
                  encoding="utf-8") as f:
            self.config = json.loads(f.read())

    # 定义请求头
    def setHeaders(self):
        headers = {
            'Host': 'h5.ubanquan.cn',
            'Connection': 'keep-alive',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
            'requestChannel': 'UBQ_H5',
            'sec-ch-ua-mobile': '?1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Mobile Safari/537.36',
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json, text/plain, */*',
            'sec-ch-ua-platform': '"Android"',
            # 'Origin': 'https://ubanquan.cn',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://h5.ubanquan.cn/home',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        return headers

    def md5(self, text: str):
        return hashlib.md5(text.encode(encoding='utf-8')).hexdigest()

    # 登录获取cookie
    def login(self):
        user = self.config.get("user")
        password = self.config.get("password")
        data = {
            "user": user,
            "password": self.md5(password)
        }
        url = 'https://ubanquan.cn/api/opuser/loginPassword'
        ret = requests.post(url=url, data=json.dumps(data), headers=self.setHeaders()).json()
        # print(ret)
        token = ret.get('data', {}).get('token')
        cookies = 'token=' + token
        self.config['cookies'] = cookies
        self.config['token'] = token
        # with open("./config.json", "w", encoding="utf-8") as f:
        #     json.dump(config, f)

    # 获取发现页的全部在售商品
    def getList(self, name):
        # 定义post数据
        def setData(pageNum):
            data = {"name": name,
                    "pageNum": pageNum,
                    "pageSize": 20,
                    "productFilterEnum": "high_price",
                    "sort": "asc",
                    "status": '1',
                    "fieldKeys": None,
                    "themeKeys": None,
                    "isPrivilege": None,
                    "terminal": "H5"
                    }
            return data

        headers = self.setHeaders()
        # headers['cookies'] = config['cookies']
        # headers['token'] = config['token']
        url = "https://h5.ubanquan.cn/api/opactivity/discoverView/v2/pageAuctionProducts"
        page = 1
        fails = 0
        # 遍历所有页的商品
        items = []
        while True:
            ret = requests.post(url, data=json.dumps(setData(page)), headers=headers).json()
            if ret.get('success'):
                totalPages = ret.get('totalPages')
                itemsList = ret.get('data', {})
                items += itemsList
                # for one in itemsList:
                #     items.append(f'{one.get("name")}:\t\t￥{one.get("nowBid") / 100.0}\n')
                # print(one.get('name'), '价格', one.get('nowBid') / 100.0)
                print(f'获取商品成功 {page}/{totalPages}')
                page += 1
                if page > 1:
                    # with open("./current.txt", "w", encoding="utf-8") as f:
                    #     f.writelines(items)
                    return items
            else:
                print(f'获取商品失败')
                fails += 1
                if fails >= 50:
                    break
                sleep(2)

    def getItemInfo(self, auctionNo):
        url = f'https://ubanquan.cn/api/opactivity/discoverView/getAuctionDetailApp/{auctionNo}'
        ret = requests.get(url=url, headers=self.setHeaders()).json()
        # print(ret)
        itemInfo = ret.get('data', {})
        if ret.get('success'):
            # print(f"序列号\t{itemInfo.get('serialNum')}\t作品名称\t{itemInfo.get('name')}")
            # print(f"当前价格\t{itemInfo.get('nowBid') / 100.0}\t加价幅度\t{itemInfo.get('accumulatePrice') / 100.0}")
            return itemInfo
        else:
            print(f"获取商品 {auctionNo} 失败")
            return None

    def justBuyIt(self, itemInfo):
        url = 'https://h5.ubanquan.cn/api/opactivity/auctionSession/biddingByBalance'
        data = {
            "amount": itemInfo["nowBid"],
            "bizId": itemInfo["sessionNo"],
            "tradePassword": self.md5(self.config['payPassword']),
            "businessInfo": "",
            "paymentScene": "BIDDING"
        }
        referer = f'https://h5.ubanquan.cn/auction/AuctionPayOrder?sessionNo={itemInfo["sessionNo"]}&themeName={quote(itemInfo["auctionInfo"]["themeName"])}&nftNumber={quote(itemInfo["auctionInfo"]["serialNum"])}&name={quote(itemInfo["name"])}&price={itemInfo["nowBid"]}&auctionNo={itemInfo["auctionInfo"]["auctionNo"]}'
        headers = self.setHeaders()
        headers['cookies'] = self.config['cookies']
        headers['token'] = self.config['token']
        headers['Referer'] = referer
        ret = requests.post(url=url, data=json.dumps(data), headers=headers).json()
        print(ret)
        return ret

    def task(self, one):
        msg = []
        name = one[0]
        myPrice = one[1]
        list = self.getList(name)
        for i in list[:5]:
            itemInfo = self.getItemInfo(i.get('auctionNo'))
            if itemInfo is not None:
                id, name, price = itemInfo.get('auctionInfo', {}).get('serialNum'), itemInfo.get(
                    'name'), itemInfo.get(
                    'nowBid') / 100.0
                if price == 0 or price <= myPrice:
                    ret = self.justBuyIt(itemInfo)
                    if ret.get('success'):
                        tmpmsg = "买到了"
                    else:
                        tmpmsg = "没抢到"
                    print(tmpmsg)
                    msg.append({"name": f"{name}", "value": f"￥{price} {tmpmsg}"})
                else:
                    # msg.append({"name": f"{name}", "value": f"￥{price} 价格不够美丽"})
                    print(f"{name} ￥{price} 价格不够美丽")

        if msg and self.config.get('push'):
            msg = "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])
            self.send(msg)


    def send(self, content):
        print("企业微信应用消息推送开始")
        qywx_corpid = self.config.get('corpid')
        qywx_agentid = self.config.get('agentid')
        qywx_corpsecret = self.config.get('corpsecret')
        qywx_touser = self.config.get('touser')
        res = requests.get(
            f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={qywx_corpid}&corpsecret={qywx_corpsecret}"
        )
        token = res.json().get("access_token", False)
        data = {
            "touser": qywx_touser,
            "agentid": int(qywx_agentid),
            "msgtype": "textcard",
            "textcard": {
                "title": "Ubanquan",
                "description": content,
                "url": "https://h5.ubanquan.cn/home",
            },
        }
        requests.post(url=f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}",
                      data=json.dumps(data))
        return


    def run(self):
        self.login()
        t1 = perf_counter()
        while True:
            t2 = perf_counter()
            # self.task()
            threads = [threading.Thread(target=self.task(one)) for one in cart.myList]
            [thread.setDaemon(True) for thread in threads]
            [thread.start() for thread in threads]
            # sleepTime = 0.05 + random.randint(0, 2) * 0.05
            # sleep(sleepTime)
            if t2 - t1 > 1800:
                self.login()
                t1 = t2


if __name__ == "__main__":
    ubanquan = ubanquan()
    ubanquan.run()
