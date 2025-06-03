from bs4 import BeautifulSoup
import os

bs = BeautifulSoup(open("docs/index.html", "r").read(), features="html.parser")
tags = bs.select("body > main > div > article")
res = []
for t in tags[1:6]:
    tt = t.select_one("div.article-header > h1 > a")
    create_time = t.select_one("p > span.article-date > a > time").attrs['datetime'].strip()
    create_time = " ".join(create_time.split(" ")[:1])
    res.append(f'<li><a target="_blank" href="https://wymli.github.io{tt.attrs['href']}">{tt.text} | {create_time}</a></li>')
print(res)

x = "\n\t\t".join(res)

tmpl = f'''
<div style="display:inline-block;background-color:#432; padding:5px ;margin:2px;width:200px" >
    <img src="devops-old-way.gif" width=40% style="float:left"/>
    <img src="TDD.png" width=40% style="float:left" />
</div>
<br>

<div style="display:inline-block;background-color:#22a ;padding:5px;width:200px">

## Hi there 👋
<img align="right" src="https://github-readme-stats.vercel.app/api?username=wymli&show_icons=true&icon_color=805AD5&text_color=718096&bg_color=ffffff&hide_title=true" width=60%/>
<img align="right" src="https://github-readme-stats.vercel.app/api/top-langs/?username=wymli&layout=compact&hide_title=true" width=60% />
<p>找工作...</p>

<div style="border: 5px solid; width: 100px">
    <div>
        <a href="https://wymli.github.io/">技术博客</a>
    </div>
    <div>
        Recent Posts:
        {x}
        <li><a href="https://wymli.github.io/">...</a></li>
    </div>
</div>

</div>
'''

open("./wymli/README.md", "w").write(tmpl)