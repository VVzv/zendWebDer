# zendWebDer
利用在线解密网站对zend加密文件进行批量解密。
## 使用方法
安装第三方依赖库:
```
pip3 install requests
pip3 install ddddocr
```
使用方法：
```
只需要修改源代码中下面两个变量内容即可，或者在该脚本的目录下创建一个source和destination目录，source目录放入zend文加密的件即可。
src_file_dir = "./source" # zend加密文件所在目录
des_file_dir = "./destination" # 解密文件保存目录
```
