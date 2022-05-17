# !/usr/bin/python
# -*- coding:utf-8 -*-
# __Author__: VVzv
import os
import sys
import time
import shutil
import random
import requests

import ddddocr

from header import randUserAgentNoTitle


org_url = "http://dezend.qiling.org"
upload_url = "http://dezend.qiling.org/api.php?op=upload"
de_up_file_url = "http://dezend.qiling.org/api.php?op=ajax_decode"
captcha = "http://dezend.qiling.org/api.php?op=captcha"


def dirExist(des_file):
    filename_file = des_file.split("/")[-1]
    file_dir = des_file.replace(filename_file, "")
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

def fileFilter(src_file_dir, des_file_dir):
    src_file_list = []
    for root, dirs, files in os.walk(src_file_dir):
        for file in files:
            filename = os.path.join(root, file)
            if os.path.splitext(file)[1] == '.php':  # 只读出php文件进行解密
                src_file_list.append(filename)
            else:
                des_filename = filename.replace(src_file_dir, des_file_dir)
                dirExist(des_filename)
                shutil.copy(filename, des_filename)
    return src_file_list

def upFile(session, file, headers, src_dir, des_dir, index=0):
    if index == 5:
        print("\033[31m[!!!] 文件上传失败次数过多，程序暂停。\033[0m")
        sys.exit(0)
    des_file_name = file.replace(src_dir, des_dir)
    if os.path.exists(des_file_name):
        return [0, 0, 0]
    filename = file.split("/")[-1]
    file_context = open(file, "rb").read()
    if b"<?php @Zend;" not in file_context and b"Zend\x00" not in file_context: # 判断php文件是否为zend加密的
        dirExist(des_file_name)
        shutil.copy(file, des_file_name)
        return [0, 0, 0]
    print("\033[36m[*] 正在进行解密的文件是：{}\033[0m".format(file))
    files = {
        "file": (filename, file_context, "text/php"),
    }
    up_res = session.post(upload_url, headers=headers, files=files)
    if up_res.status_code == 200:
        up_res_rel = up_res.json()
        get_zend_type = up_res_rel["data"]["type"]
        is_zend = get_zend_type.split("|")[0]
        zend_php_ver = get_zend_type.split("|")[-1]
        up_file_url = up_res_rel["url"]
        if "zend" == is_zend:
            if int(zend_php_ver) <= 54:
                return [filename, up_file_url, get_zend_type]
            else:
                print("\033[35mzend加密时的PHP版本过高[{}]\033[0m".format(zend_php_ver))
                sys.exit(0)
        else:
            print("\033[35m不是zend加密[{}]\033[0m".format(is_zend))
            sys.exit(0)
    else:
        return upFile(session, file, headers, src_dir, des_dir, index+1)

def ckCap(session, headers, index=0):
    if index == 5:
        print("\033[31m[!!!] 验证码获取失败次数过多，程序暂停。\033[0m")
        sys.exit(0)
    c_res = session.get(captcha, headers=headers)
    # with open("111.png", "wb") as f:
    #     f.write(c_res.content)
    if c_res.status_code == 200:
        orc = ddddocr.DdddOcr(show_ad=False)
        try:
            c = orc.classification(c_res.content)
            return c
        except:
            return ckCap(session, headers, index+1)
    else:
        return ckCap(session, headers, index+1)


def defile2down(session, up_info, c, filename, headers, src_file_dir, des_file_dir, index=0):
    '''
    param: session: 回话session
    param: up_info: upFile函数返回的结果
    param: c: ckCap返回的验证码
    param: filename: 文件全称（包含路径）
    param: headers: 请求头（每次做一个文件请求换一个UA头）
    param: src_file_dir: 文件源目录
    param: des_file_dir: 文件保存目录
    param: index: 计次，防止验证码失败一直循环（默认10次终止程序）
    '''
    if index == 10:
        print("\033[31m[!!!] 验证码识别次数过多，程序暂停。\033[0m")
        sys.exit(0)
    data = {
        "name": up_info[0],
        "path": up_info[1],
        "type": up_info[2],
        "captcha": c,
    }
    decode_file = session.post(de_up_file_url, headers=headers, data=data)
    if decode_file.status_code == 200:
        decode_info = decode_file.json()
        ck_code = int(decode_info["code"])
        if ck_code == 1:
            down_url = decode_info["url"]
            down_de_f_url = org_url + down_url
            res = session.get(down_de_f_url, headers=headers)
            if res.status_code == 200:
                down_save_file = filename.replace(src_file_dir, des_file_dir)
                print("\033[32m[+] {}解密成功，文件保存到{}\033[0m".format(up_info[0], down_save_file))
                dirExist(down_save_file)
                with open(down_save_file, "w") as f:
                    f.write(res.text)
        else:
            error_msg = decode_info["msg"]
            if "解密失败" not in error_msg:
                c = ckCap(session, headers)
                time.sleep(0.5)
                return defile2down(session, up_info, c, filename, headers, src_file_dir, des_file_dir, index+1)
            else:
                print("\033[35m[-] 解密失败[{}]\033[0m".format(filename))

if __name__ == '__main__':
    # 文件目录结尾不用加斜杠
    src_file_dir = "./source"  # 源文件路径（zend加密目录）
    des_file_dir = "./destination" # 目的文件路径（zend解密目录）
    f_list = fileFilter(src_file_dir, des_file_dir)
    rand_time_list = [0.1, 0.2, 0.3]
    min_time = (len(f_list)*3)/60
    h_time = min_time / 60
    print("[*] 共统计需解密文件{}，预计用时{}时{}分.".format(len(f_list), h_time, min_time))
    for f in f_list:
        headers = {
            "User-Agent": randUserAgentNoTitle(),
            "Referer": "http://dezend.qiling.org/free/",
            "X-FORWARDED-FOR": "127.0.0.1",
        }
        time.sleep(random.choice(rand_time_list))
        session = requests.Session()
        up_f_r = upFile(session, f, headers, src_file_dir, des_file_dir)
        if up_f_r[0] == 0:
            continue
        c = ckCap(session, headers)
        defile2down(session, up_f_r, c, f, headers, src_file_dir, des_file_dir)



