# HTTP 网络代理服务器实验代码

这是一个简单的 HTTP 网络代理服务器 的 Python 实现

## 本代理服务器实现的功能有：

1. 监听本地 `8888` 号端口，然后接收用户浏览器的请求，并将其与服务器端进行通信，再将请求到的内容分发给用户浏览器
2. 过滤特定域名的访问。用户可以通过往与 .py 文件同目录下的 `blacklists.txt` 中添加域名（支持正则表达式）来实现对特定域名的过滤
3. 过滤特定用户访问外部网站。代理服务器管理员可以通过往 `blockusers.txt` 中添加用户名来实现对特定用户的屏蔽

## 使用方法

1. 首先，确保你的电脑上安装了 Python 3.7 及以上版本
2. 克隆本仓库的代码
3. 在系统设置中开启代理服务器，地址填 `127.0.0.1` 或 `localhost`，端口填 `8888`
4. 在克隆下来的代码目录中，双击运行 `http_main.py` 文件即可

## 关于

本项目是吉首大学2022级学生李悠然的计算机网络实验作业（第一部分）
本项目使用 VSCode 编辑器进行开发
作者的学号：2022405532
谢谢使用，祝万事如意