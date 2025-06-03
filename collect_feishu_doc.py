import requests
import json

r = requests.get(
    "https://c6t4wbgxht.feishu.cn/space/api/explorer/v3/children/list/?thumbnail_width=1028&thumbnail_height=1028&thumbnail_policy=4&obj_type=0&obj_type=2&obj_type=22&obj_type=44&obj_type=3&obj_type=30&obj_type=8&obj_type=11&obj_type=12&obj_type=84&length=50&asc=0&rank=0&token=Sq6TfjSOZlFPtwd2m6icv3h9nEb&interflow_filter=CLIENT_VARS",
    headers={
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    },
).json()


print(json.dumps(r, indent=4))
