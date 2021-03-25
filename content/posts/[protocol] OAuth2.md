---
title: "[protocol] OAuth2"
date: 2021-03-25
tags: ["protocol"]
categories: ["protocol"]
---

# OAuth2.0

open authority 2.0,开放授权

主要用于A网站向某个常用第三方社交网站请求用户信息,第三方社交网站需要给予A网站用户信息,这必须有用户的授权才行,但是如果直接给予A网站用户的用户名密码,又太不安全,并且我们希望只提供给A网站受限的资源访问权限,比如只能获取到用户名等.因此需要使用OAuth2.0

> ref: 
>
> https://aaronparecki.com/oauth-2-simplified/#web-server-apps
>
> https://blog.bearer.sh/understanding-auth-part-1-what-is-oauth/

## 多种授权模式

客户端必须得到用户的授权（authorization grant），才能获得令牌（access token）。OAuth 2.0定义了四种授权方式。

> 这里用户的授权,是在从第三方网站跳转到社交网站进行授权,用户需在社交网站登陆,并点击授权

- authorization code
- implicit
- resource owner password credentials

> The authorization code grant type is the **most common variant** of OAuth 2.0

## User-Agent Flow流程

以qq的OAuth2为例,qq采用了隐式(implicit)授权(client-side模式，是[OAuth2.0认证](https://wiki.open.qq.com/wiki/mobile/OAuth2.0简介)的一种模式，又称User-Agent Flow)

即不涉及后端,全在浏览器操作

### A网站向第三方注册

对于要使用第三方登陆功能的web service(此时,社交网站是第三方),必须先向第三方社交网站注册自己,获得唯一的`Client ID and Secret`,以qq第三方登陆为例,将会获得唯一的`appid and apikey`

> 对于secret/apikey必须机密保存在后端,如果是前端单页面服务,没有后端,则不应该向它们发送密钥,使用PKCE拓展

> 似乎 Client ID and Client Secret 被称为client credentials

### 用户在A网站点击第三方登陆

前端跳转到如下URL

```
https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=CLIENT_ID&redirect_uri=REDIRECT_URI&scope=photos&state=1234zyx
```

| 参数          | isNeed |                             含义                             |
| ------------- | -----: | :----------------------------------------------------------: |
| response_type |   必须 |                授权类型，此值固定为“token”。                 |
| client_id     |   必须 |            申请QQ登录成功后，分配给应用的appid。             |
| redirect_uri  |   必须 |                    成功授权后的回调地址。                    |
| scope         |   可选 | 请求用户授权时向用户显示的可进行授权的列表。  可填写的值是[API列表](https://wiki.open.qq.com/wiki/mobile/API列表)中列出的接口，以及一些动作型的授权（目前仅有：do_like），如果要填写多个接口名称，请用逗号隔开。  例如：scope=get_user_info,list_album,upload_pic,do_like  不传则默认请求对接口get_user_info进行授权。  建议控制授权项的数量，只传入必要的接口名称，因为授权项越多，用户越可能拒绝进行任何授权。 |
| state         |   可选 | client端的状态值。用于第三方应用防止CSRF攻击，成功授权后回调时会原样带回 |

 如果用户成功登录并授权，则会跳转到指定的回调地址，并在URL后加“#”号，带上Access  Token以及expires_in等参数。如果请求参数中传入了state，这里会带上原始的state值。如果redirect_uri地址后已经有“#”号，则加“&”号，带上相应的返回参数。如：
` http://graph.qq.com/demo/index.jsp?#access_token=FE04************************CCE2&expires_in=7776000&state=test`

> expires_in是该access token的有效期，单位为秒。 

Tips：

1. 可通过js方法：window.location.hash来获取URL中#后的参数值。
2. 建议用js设置cookie存储token。

### 获取openID

> openid是qq用户的唯一标识

拿到access_token后,get如下的url:

`https://graph.qq.com/oauth2.0/me?access_token=YOUR_ACCESS_TOKEN `

返回

```
callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} ); 
```

### 获取用户信息

获得用户标识openid后,get如下url:

```
https://graph.qq.com/user/get_simple_userinfo?access_token=1234ABD1234ABD&oauth_consumer_key=12345& openid=B08D412EEC4000FFC37CAABBDC1234CC&format=json 
```

| 参数               | 含义                                                         |
| ------------------ | ------------------------------------------------------------ |
| access_token       | 可通过[使用Implicit Grant方式获取Access Token](https://wiki.open.qq.com/wiki/mobile/使用Implicit_Grant方式获取Access_Token)来获取。  access_token有3个月有效期。 |
| oauth_consumer_key | 申请QQ登录成功后，分配给应用的appid(即client_id)             |
| openid             | 用户的ID，与QQ号码一一对应。  可通过调用https://graph.qq.com/oauth2.0/me?access_token=YOUR_ACCESS_TOKEN 来获取。 |

> 注意,不是直接返回用户信息,而是让网站自己去请求



### 注意

**Implicit** was previously recommended for clients without a secret, but has been __superseded__ by using the Authorization Code grant with PKCE.



## 授权码流程

参考上述的User-Agent Flow,在第一次访问授权服务的时候,不直接返回access_token,而是返回一个授权码

接着,我们拿这个授权码去得到access_token

```
POST https://api.authorization-server.com/token?
  grant_type=authorization_code&
  code=AUTH_CODE_HERE&
  redirect_uri=REDIRECT_URI&
  client_id=CLIENT_ID&
  client_secret=CLIENT_SECRET
```

因为是server发起的,所以可以带上secret

响应:

```
{
  "access_token":"RsT5OjbzRn430zqMLgV3Ia",
  "expires_in":3600
}
```

> 为什么不直接返回access_token? 因为不安全,我们希望access_token只在后端持有,所以多了一步用code换access_token的步骤

## Legs

implicit和authority code都是three-legs,即都需要用户的参与

2-legs的使用场景和第三方登陆无关,故不讨论

> Three legged does not imply a certain type of app as in "browser  based". Three legged means that an application acts on the direct behalf of a user. In the three legged scenarios there is  
>
> 1. an application (consumer),  
> 2. a user (resource owner) and
> 3. an API (service provider).
>
> In two legged scenarios there is no concept of a user. Typically this has to do with application-to-application solutions. There the  application (consumer) acts on behalf of itself. So in two legged OAuth, there is:
>
> 1. an application (consumer),
> 2. an API (service provider)
>
> The difference is simply that there is no need of a user authorisation step in the 2-legged approach.