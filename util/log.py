#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :log.py
# @Time      :2025/1/23 18:19
# @Author    : https://github.com/vincenschan/InvinRAG
# @Description

# 1、配置日志要保存的文件夹，创建文件夹
import time
import os
import logging
import threading
import os

BASE_LOG_DIR = os.path.join('logs')
error_path = os.path.join('error')
if not os.path.exists(error_path):
    # 如果logs/error/不存在，递归创建目录
    os.makedirs(error_path)

all_path = os.path.join(BASE_LOG_DIR, 'all')
if not os.path.exists(all_path):
    # 如果logs/all/目录不存在，就递归创建(如果logs目录不存在，也会创建)
    os.makedirs(all_path)

# 2、相关的日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # 设置已存在的logger不失效
    'filters': {
    },
    'formatters': {
        'standard': {
            'format': '[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d:%(funcName)s]：%(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '[%(asctime)s][%(levelname)s]：%(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {  # 按照文件大小分割日志，将所有的日志信息都保存在这里
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_LOG_DIR, 'all', 'debug.log'),
            'maxBytes': 1024 * 1024 * 50,  # 日志大小50M
            'backupCount': 5,
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
        'time_file': {  # 按照时间分割日志，每周一新增一个日志文件，存error等级以上的日志
            'level': 'INFO',  # 日志的等级
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_LOG_DIR, 'error', f"{time.strftime('%Y-%m-%d')}.log"),  # 日志的文件名
            'when': 'D',  # 时间单位，M,H,D,'W0'(星期1),'W6'（星期天）
            'interval': 1,
            'backupCount': 5,  # 备份数量
            'formatter': 'standard',  # 使用的日志格式
            'encoding': 'utf-8',
        }

    },
    'loggers': {
        # INFO以上日志，打印在console，也写到以文件大小分割的日志中
        'django': {
            'handlers': ['console', 'file'],  # handlers中存在的配置
            'level': 'INFO',
            'propagate': True
        },
        # error以上的日志写到按时间分割的日志文件中，同时打印在控制台
        'django.request': {
            'handlers': ['console', 'time_file'],  # handlers中存在的配置
            'level': 'ERROR',
            'propagate': True
        },

    },
}


class CustomFormatter(logging.Formatter):
    def format(self, record):
        process_id = os.getpid()
        thread_id = threading.get_ident()
        record.process_id = process_id
        record.thread_id = thread_id
        return super().format(record)


def logHander(name):
    # 创建日志记录器
    logger = logging.getLogger(name)

    # 配置日志记录器
    logger.setLevel(logging.INFO)

    # 创建文件处理程序
    file_handler = logging.FileHandler('logs/loging.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 创建控制台处理程序
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 创建日志格式器
    formatter = CustomFormatter('%(asctime)s [%(levelname)s][%(name)s][%(process_id)s:%(thread_id)s]:%(message)s')

    # 将格式器添加到处理程序
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 将处理程序添加到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


if __name__ == "__main__":
    pass
