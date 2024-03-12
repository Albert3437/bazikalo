from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from loguru import logger
from openai import OpenAI

from db import PostDatabase
from tg import *

import configparser
import feedparser
import threading
import requests
import time


config = configparser.ConfigParser()
config.read('config.ini')

logger.add(config['Settings']['log_file_name'])


def get_post_time(db, create_time):
    data = db.read_all_records()
    if len(data) == 0:
        return datetime.now()
    data = [dat for dat in data if dat['active']]
    data.sort(key=lambda x: x['post_time'])
    create_time = datetime.strptime(create_time, "%a, %d %b %Y %H:%M:%S GMT")
    try:
        last_post_time = datetime.strptime(data[-1]['post_time'], "%Y-%m-%d %H:%M:%S.%f")
    except:
        last_post_time = datetime.strptime(data[-1]['post_time'], "%Y-%m-%d %H:%M:%S")
    if create_time + timedelta(hours=5) > last_post_time + timedelta(hours=1):
        return last_post_time + timedelta(hours=1)
    return create_time + timedelta(hours=5)


def get_articles(*, feed_url = config['Links']['RSS_news'], keys_list=['title', 'link', 'published', 'media_content']):
    articles = []
    feed = feedparser.parse(feed_url)
    for article in feed.entries:
        new_dict = {}
        for key in keys_list:
            try:
                new_dict[key] = article[key]
            except Exception as e:
                logger.error(e)
        articles.append(new_dict)
    return articles


def get_page_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        html_content = response.content

        soup = BeautifulSoup(html_content, 'html.parser')

        paragraphs = soup.find_all('p')
        new_string = ''

        for paragraph in paragraphs:
            if 'всі права захищені' not in paragraph.text.lower():
                new_string += '\n' + paragraph.text
        
        return new_string

    else:
        print('Ошибка при получении страницы:', response.status_code)


def gpt_response(text):
    try:
        client = OpenAI(api_key=config['ApiKeys']['gpt_token'])
        response = client.chat.completions.create(model=config['Settings']['gpt_model'],
        messages=[
            {"role": "system", "content": config['Settings']['gpt_response']},
            {"role": "user", "content": text},
        ])
        return response.choices[0].message.content
    except Exception as e:
        logger.warning(e)
        return 'Fail'


def run():
    old_articles = []
    
    while True:
        try:
            articles = get_articles()
            db = PostDatabase()
            old_articles = db.read_all_records()
            old_articles = [dat['title'] for dat in old_articles]
            db.close()
            unique_articles = [article for article in articles if article['title'] not in old_articles]
            for article in unique_articles:
                try:
                    data = get_page_data(article['link'])
                    text_prewiev = gpt_response(data)
                    article['short_data'] = text_prewiev
                    if text_prewiev != 'Fail':
                        db = PostDatabase()
                        post_time = get_post_time(db, article['published'])
                        db.add_record(article['title'], article['short_data'], article['media_content'][0]['url'], post_time)
                        send_test_article(db.get_last_id(), f'*{article['title']}*\n\n{article['short_data']}\n\nПост будет размещен {post_time}', article['media_content'][0]['url'])
                        db.close()
                except Exception as e:
                    logger.error(e)
            time.sleep(config['Settings']['sleep_time'])
        except Exception as e:
            logger.error(e)
            time.sleep(10)

def run_posting():
    while True:
        db = PostDatabase()
        data = db.read_all_records()
        db.close()
        data = [art for art in data if art['active']]


        for article in data:
            try:
                post_time = datetime.strptime(article['post_time'], "%Y-%m-%d %H:%M:%S.%f")
            except:
                post_time = datetime.strptime(article['post_time'], "%Y-%m-%d %H:%M:%S")
            if post_time < datetime.now():
                try:
                    send_article(f'*{article['title']}*\n\n{article['text']}', article['photo_url']) # Сдесь настраивать финальный формат постов
                except Exception as e:
                    logger.warning(e)
                db = PostDatabase()
                db.update_active_status(article['id'], 0)
                db.close()
        time.sleep(int(config['Settings']['check_post_timeout']))

if __name__ == '__main__':
    main_thread = threading.Thread(target=run)
    tg_thread = threading.Thread(target=bot.polling)
    posting_thread = threading.Thread(target=run_posting)
    main_thread.start()
    tg_thread.start()
    posting_thread.start()
    main_thread.join()
    tg_thread.join()
    posting_thread.join()



# Автоновоснтник работает, теперь надо проработать автопостинг новостей
# должен быть отдельный поток который будет отслеживать время постинга
# и если время настало и пост должен быть запощен то он постится, 
# так же возможно потребуется добавить столбец в базу данных с 
# в которой будет указано запощена статья или нет,
# так же надо продумать функцию с определением времени для постинга