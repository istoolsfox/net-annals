#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时工具：批量实测 URL 状态码（带浏览器 UA），只读本文件入参。"""
import sys, json, urllib.request, ssl

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

def check(url, timeout=15):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            body = r.read(600)
            return r.status, body[:120].decode("utf-8", "ignore")
    except Exception as exc:
        # 30x 手动跟一跳
        try:
            opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler(), urllib.request.HTTPSHandler(context=CTX))
            with opener.open(req, timeout=timeout) as r:
                return r.status, "(redirected) " + r.geturl()[:100]
        except Exception as exc2:
            return None, f"{type(exc).__name__}: {exc2}"

if __name__ == "__main__":
    urls = [u.strip() for u in sys.stdin.read().splitlines() if u.strip()]
    for u in urls:
        st, note = check(u)
        print(f"{st}\t{note}\t{u}")
