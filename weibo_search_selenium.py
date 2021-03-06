#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas
import time
import datetime
import re
import random
import logging
from selenium import webdriver

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('window-size=1200,1100')
driver = webdriver.Chrome(chrome_options=chrome_options,executable_path='D:/chromedriver/chromedriver.exe')
# driver = webdriver.Chrome('D:/chromedriver/chromedriver.exe')
df = pandas.DataFrame()
# driver.maximize_window()

# 登录
def LoginWeibo(username, password):
    try:
        driver.get('http://www.weibo.com/login.php')
        time.sleep(5)
        driver.find_element_by_xpath('//input[@id="loginname"]').clear()
        driver.find_element_by_xpath('//input[@id="loginname"]').send_keys(username)
        time.sleep(3)
        driver.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[2]/div/input').send_keys(password)
        driver.find_element_by_xpath('//*[@id="login_form_savestate"]').click()
        time.sleep(1)
        driver.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[6]/a').click()
    except Exception:
        logger.error('Something wrong with', exc_info=True)

# 搜索，如果大于一天，分天搜索
def GetSearchContent(key):
    driver.get("http://s.weibo.com/")
    logger.info('搜索热点主题：%s' % key)
    driver.find_element_by_xpath("//input").send_keys(key)
    time.sleep(3)
    driver.find_element_by_xpath('//button').click()
    current_url = driver.current_url.split('&')[0]
    start_date = datetime.datetime(2018,10,18,0)
    end_date = datetime.datetime(2018,10,18,23)
    delta_date = datetime.timedelta(hours=23)
    start_stamp = start_date
    end_stamp = start_date + delta_date
    while end_stamp <= end_date:
        url = current_url + '&typeall=1&suball=1&timescope=custom:' + str(start_stamp.strftime("%Y-%m-%d")) + ':' + str(end_stamp.strftime("%Y-%m-%d")) + '&Refer=g'
        time.sleep(random.randint(5,10))
        driver.get(url)
        handlePage()
        start_stamp = end_stamp + datetime.timedelta(hours=1)
        end_stamp = start_stamp + delta_date

# 处理页面，检查是否有内容，有内容进行爬取
def handlePage():
    page = 1
    while True:
        time.sleep(random.randint(5,10))
        if checkContent():
            logger.info('页数:%s' % page)
            getContent()
            page += 1
            if checkNext():
                driver.find_element_by_xpath('//div[@class="m-page"]/div/a[@class="next"]').click()
            else:
                logger.info("no Next")
                break
        else:
            logger.info("no Content")
            break

# 检查页面是否有内容
def checkContent():
    try:
        driver.find_element_by_xpath("//div[@class='card card-no-result s-pt20b40']")
        flag = False
    except:
        flag = True
    return flag

# 检查是否有下一页
def checkNext():
    try:
        driver.find_element_by_xpath('//div[@class="m-page"]/div/a[@class="next"]')
        flag = True
    except:
        flag = False
    return flag

# 处理时间
def get_datetime(s):
    try:
        today = datetime.datetime.today()
        if '今天' in s:
            H, M = re.findall(r'\d+',s)
            date = datetime.datetime(today.year, today.month, today.day, int(H), int(M)).strftime('%Y-%m-%d %H:%M')
        elif '年' in s:
            y, m, d, H, M = re.findall(r'\d+',s)
            date = datetime.datetime(int(y), int(m), int(d), int(H), int(M)).strftime('%Y-%m-%d %H:%M')                       
        else:    
            m, d, H, M = re.findall(r'\d+',s)
            date = datetime.datetime(today.year, int(m), int(d), int(H), int(M)).strftime('%Y-%m-%d %H:%M')
    except:
        date = s
    return date

# 获取内容
def getContent():
    nodes = driver.find_elements_by_xpath('//div[@class="card-wrap"][@action-type="feed_list_item"][@mid]')
    if len(nodes) == 0:
        time.sleep(random.randint(20,30))
        driver.get(driver.current_url)
        getContent()
    results = []
    global df
    logger.info('微博数量：%s' % len(nodes))
    for i in range(len(nodes)):
        blog = {}
        try:
            BZNC = nodes[i].find_element_by_xpath('.//a[@class="name"]').get_attribute('nick-name')
        except:
            BZNC = ''
        blog['博主昵称'] = BZNC
        try:
            BZZY = nodes[i].find_element_by_xpath('.//a[@class="name"]').get_attribute("href")
        except:
            BZZY = ''
        blog['博主主页'] = BZZY
        try:
            WBNR = nodes[i].find_element_by_xpath('.//p[@class="txt"][@node-type="feed_list_content"]').text
            if len(nodes[i].find_elements_by_xpath('.//p[@class="txt"][@node-type="feed_list_content"]'))>1:
                WBNR = WBNR + '\n转发：' +nodes[i].find_element_by_xpath('.//div[@node-type="feed_list_forwardContent"]').text
        except:
            WBNR = ''
        blog['微博内容'] = WBNR
        try:
            FBSJ = nodes[i].find_element_by_xpath('.//div[@class="content"]/p[@class="from"]/a[1]').text
        except:
            FBSJ = ''
        blog['发布时间'] = get_datetime(FBSJ)
        try:
            WBDZ = nodes[i].find_element_by_xpath('.//div[@class="content"]/p[@class="from"]/a[1]').get_attribute("href")
        except:
            WBDZ = ''
        blog['微博地址'] = WBDZ
        try:
            WBLY = nodes[i].find_element_by_xpath('.//div[@class="content"]/p[@class="from"]/a[2]').text
        except:
            WBLY = ''
        blog['微博来源'] = WBLY
        try:
            ZF_TEXT = nodes[i].find_element_by_xpath('.//div[@class="card-act"]/ul/li[2]').text.replace('转发','').strip()
            if ZF_TEXT == '':
                ZF = 0
            else:
                ZF = int(ZF_TEXT)
        except:
            ZF = 0
        blog['转发'] = ZF
        try:
            PL_TEXT = nodes[i].find_element_by_xpath('.//div[@class="card-act"]/ul/li[3]').text.replace('评论','').strip()
            if PL_TEXT == '':
                PL = 0
            else:
                PL = int(PL_TEXT)
        except:
            PL = 0
        blog['评论'] = PL
        try:
            ZAN_TEXT = nodes[i].find_element_by_xpath('.//div[@class="card-act"]/ul/li[4]/a/em').text
            if ZAN_TEXT == '':
                ZAN = 0
            else:
                ZAN = int(ZAN_TEXT)
        except:
            ZAN = 0
        blog['赞'] = ZAN

        results.append(blog)
    df = df.append(results)
    df.to_excel('C:/Users/Administrator/Desktop/results.xlsx',index=0)
    logger.info('已导出微博条数：%s' % len(df))

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler('export_record.log')
    handler.setLevel(logging.INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    console.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(console)
    logger.info('*'*30+'START'+'*'*30)
    username = '******' # 填写用户名
    password = '******' # 填写密码
    LoginWeibo(username, password)
    key = 'python' # 填写搜索关键词
    GetSearchContent(key)
    time.sleep(10)
    driver.quit()
    logger.info('*'*30+'E N D'+'*'*30)
