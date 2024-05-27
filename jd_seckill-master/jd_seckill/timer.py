#!/usr/bin/env python
# -*- encoding=utf8 -*-

import time
import requests
import json

from datetime import datetime, timedelta

from .jd_logger import logger
from .config import global_config


class Timer(object):
    def __init__(self, sleep_interval=0.5):
        self.buy_time_str = global_config.getRaw('config', 'buy_time')
        self.buy_time = datetime.strptime(self.buy_time_str, "%Y-%m-%d %H:%M:%S.%f")
        self.buy_time_ms = int(time.mktime(self.buy_time.timetuple()) * 1000.0 + self.buy_time.microsecond / 1000)
        self.sleep_interval = sleep_interval
        self.diff_time = None  # 初始化时diff_time为None，将在start方法中计算

    def jd_time(self):
        """
        从京东服务器获取时间毫秒，包含错误处理
        :return:
        """
        url = 'https://a.jd.com//ajax/queryServerData.html'
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            ret = response.text
            js = json.loads(ret)
            return int(js["serverTime"])
        except requests.RequestException as e:
            logger.error(f"网络请求错误: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"解析京东服务器时间出错: {e}")
            return None

    def local_time(self):
        """
        获取本地毫秒时间
        :return:
        """
        return int(round(time.time() * 1000))

    def local_jd_time_diff(self):
        """
        计算本地与京东服务器时间差
        :return:
        """
        jd_time_ms = self.jd_time()
        if jd_time_ms is not None:
            self.diff_time = self.local_time() - jd_time_ms
            return self.diff_time
        else:
            logger.error("无法获取京东服务器时间，无法计算时间差")
            return None

    def start(self):
        # 确保diff_time已计算
        if self.diff_time is None:
            self.local_jd_time_diff()
            if self.diff_time is None:
                logger.error("无法启动，因无法获取时间差")
                return
        
        logger.info('正在等待到达设定时间:{}，检测本地时间与京东服务器时间误差为【{}】毫秒'.format(self.buy_time.strftime("%Y-%m-%d %H:%M:%S"), abs(self.diff_time)))
        
        while True:
            current_ms = self.local_time() - self.diff_time
            if current_ms >= self.buy_time_ms:
                logger.info('时间到达，开始执行……')
                break
            else:
                time.sleep(max(self.sleep_interval - ((self.sleep_interval * 0.1) if current_ms + self.sleep_interval > self.buy_time_ms else 0), 0))  # 动态调整sleep时间以接近精确到达

# 示例使用
if __name__ == "__main__":
    timer = Timer()
    timer.start()