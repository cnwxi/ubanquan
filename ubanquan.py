import hashlib
import json
import multiprocessing
from multiprocessing import Manager
import os
import time
from datetime import datetime
from time import perf_counter
from urllib.parse import quote
from ctypes import c_wchar_p
import requests
import yaml


def load():
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), './config.json'), 'r',
              encoding='utf-8') as f:
        config = json.loads(f.read())

    with open(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), './cart.yaml'), 'r', encoding='utf-8')as f:
        cart = yaml.safe_load(f.read())
    return config, cart


def md5(text: str):
    return hashlib.md5(text.encode(encoding='utf-8')).hexdigest()

    # 定义请求头


def setHeaders():
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


class uBanQuan():
    def __init__(self, config, cart, pid):
        self.config = config
        self.cart = cart
        self.pid = pid
        print(f'{self.pid} 刷单进程初始化')

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

        headers = setHeaders()
        # headers['cookies'] = config['cookies']
        # headers['token'] = config['token']
        url = "https://h5.ubanquan.cn/api/opactivity/discoverView/v2/pageAuctionProducts"
        page = 1
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
                # print(f'获取商品成功 {page}/{totalPages}')
                page += 1
                if (page > self.config['page']) or (page > totalPages):
                    # with open("./current.txt", "w", encoding="utf-8") as f:
                    #     f.writelines(items)
                    return items
            # else:
            # print(f'获取商品失败')

    def getItemInfo(self, auctionNo):
        url = f'https://ubanquan.cn/api/opactivity/discoverView/getAuctionDetailApp/{auctionNo}'
        ret = requests.get(url=url, headers=setHeaders()).json()
        # print(ret)
        itemInfo = ret.get('data', {})
        if ret.get('success'):
            # print(f"序列号\t{itemInfo.get('serialNum')}\t作品名称\t{itemInfo.get('name')}")
            # print(f"当前价格\t{itemInfo.get('nowBid') / 100.0}\t加价幅度\t{itemInfo.get('accumulatePrice') / 100.0}")
            return itemInfo
        else:
            print(f"获取商品 {auctionNo} 失败")
            return None

    def justBuyIt(self, itemInfo, token):
        url = 'https://h5.ubanquan.cn/api/opactivity/auctionSession/biddingByBalance'
        data = {
            "amount": itemInfo["nowBid"],
            "bizId": itemInfo["sessionNo"],
            "tradePassword": md5(self.config['payPassword']),
            "businessInfo": "",
            "paymentScene": "BIDDING"
        }
        referer = f'https://h5.ubanquan.cn/auction/AuctionPayOrder?sessionNo={itemInfo["sessionNo"]}&themeName={quote(itemInfo["auctionInfo"]["themeName"])}&nftNumber={quote(itemInfo["auctionInfo"]["serialNum"])}&name={quote(itemInfo["name"])}&price={itemInfo["nowBid"]}&auctionNo={itemInfo["auctionInfo"]["auctionNo"]}'
        headers = setHeaders()
        headers['cookies'] = f'token={token.value}'
        headers['token'] = token.value
        headers['Referer'] = referer
        ret = requests.post(url=url, data=json.dumps(data), headers=headers).json()
        print(ret)
        return ret

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

    def run(self, token):
        # self.count += 1
        while True:
            msg = []
            name = self.cart['name']
            myPrice = self.cart['price']
            list = self.getList(name)
            for i in list[:self.config.get('num')]:
                name = i['name']
                price = i['nowBid'] / 100.0
                if price > myPrice:
                    print(f"{self.pid} {datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')} {name} ￥{price} 价格不够美丽")
                else:
                    itemInfo = self.getItemInfo(i.get('auctionNo'))
                    if itemInfo is not None:
                        id, name, price = itemInfo.get('auctionInfo', {}).get('serialNum'), itemInfo.get(
                            'name'), itemInfo.get(
                            'nowBid') / 100.0
                        if price == 0 or price <= myPrice:
                            ret = self.justBuyIt(itemInfo=itemInfo, token=token)
                            if ret.get('success'):
                                tmpmsg = "买到了"
                            else:
                                tmpmsg = f"没抢到，errorMsg：{ret.get('errorMsg')}"
                            print(
                                f"{self.pid} {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))} {tmpmsg}")
                            msg.append({"name": f"{name}", "value": f"￥{price} {tmpmsg}"})
                        else:
                            print(
                                f"{self.pid} {datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')} {name} ￥{price} 价格不够美丽")

            if msg and self.config.get('push'):
                msg = "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])
                self.send(msg)


class init():
    def __init__(self, config, pid):
        multiprocessing.Process.__init__(self)
        self.config = config
        self.pid = pid
        print(f'{self.pid} 登录进程初始化')

    # 登录获取cookie
    def login(self, token):
        user = self.config.get("user")
        password = self.config.get("password")
        data = {
            "user": user,
            "password": md5(password)
        }
        url = 'https://ubanquan.cn/api/opuser/loginPassword'
        ret = requests.post(url=url, data=json.dumps(data), headers=setHeaders()).json()
        # print(ret)
        token.value = ret.get('data', {}).get('token')
        # cookies = 'token=' + token.value
        # print(cookies)
        # with open("./config.json", "w", encoding="utf-8") as f:
        #     json.dump(config, f)
        return ret

    def run(self, token):
        ret = self.login(token)
        if ret.get('success'):
            print(f"{self.pid} {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))} 登录成功")
            token.value = ret.get('data', {}).get('token')
            t1 = perf_counter()
            while True:
                t2 = perf_counter()
                # 超时重登 单位 秒/s
                if t2 - t1 > 5:
                    t1 = t2
                    ret = self.login(token)
                    if ret.get('success'):
                        token.value = ret.get('data', {}).get('token')
                        print(
                            f"{self.pid} {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))} 重新登录刷新token")
                    else:
                        quit()


if __name__ == "__main__":
    config, cart = load()
    token = Manager().Value(c_wchar_p, '')
    p0 = multiprocessing.Process(target=init(config=config, pid=0).run, args=(token,))

    plist = []
    process = config.get('process')
    pid = 1
    for i in range(process):
        for j in cart:
            plist.append(
                multiprocessing.Process(target=uBanQuan(config=config, cart=cart[j], pid=pid).run, args=(token,)))
            pid += 1
    p0.start()
    [p.start() for p in plist]
    p0.join()
    [p.join() for p in plist]
