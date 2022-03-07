uBanQuan
一份用来刷优版权nft藏品的代码
1、请修改 config_example.json 文件中的参数后，将文件名修改为 config.json
1.1、参数解释：
  "user"        ——账户，一般是手机号
  "password"    ——登录密码
  "payPassword" ——支付密码
  "push"        ——是否开启企业微信推送，true或者false
  "corpid"      ——企业微信推送参数：企业ID
  "agentid"     ——企业微信推送参数：企业应用ID
  "corpsecret"  ——企业微信推送参数：企业应用密钥
  "touser"      ——推送范围，默认"@all"，推送全体
  "page"        ——获取商品列表页数，每页20个商品，填入数字即可
  "num"         ——获取需要的商品个数，填入数字即可
  "process"     —开启多进程，cart.yaml中n个商品，process设置为m，会开启n*m个进程
2、想要购买的藏品和对应价格请于 cart.yaml 中添加
PS：注意保持配置文件的格式

· 仅供学习交流，严禁用于商业用途，请于24小时内删除
