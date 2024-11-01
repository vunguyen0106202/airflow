from gc import get_stats
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import requests
import json
import os
import logging
import re
from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

ads_manager_url = 'https://adsmanager.facebook.com/adsmanager/manage/ad_account_settings/ad_account_setup?act=264708371188743'
request_url_head = 'https://graph.facebook.com/v20.0/'
like = 'reactions.as(fb_preactions_like).type(LIKE).limit(0).summary(total_count)'
love = 'reactions.as(fb_preactions_love).type(LOVE).limit(0).summary(total_count)'
wow = 'reactions.as(fb_preactions_wow).type(WOW).limit(0).summary(total_count)'
haha = 'reactions.as(fb_preactions_haha).type(HAHA).limit(0).summary(total_count)'
sad = 'reactions.as(fb_preactions_sad).type(SAD).limit(0).summary(total_count)'
angry = 'reactions.as(fb_preactions_angry).type(ANGRY).limit(0).summary(total_count)'
reactions_count_field = f'reactions.as(fb_preactions_total).limit(0).summary(total_count)%2C{like}%2C{love}%2C{wow}%2C{haha}%2C{sad}%2C{angry}'

key_mapping = {
    "posts": "fb_posts",
    "comments": "fb_pcomments",
    "full_picture": "fb_pfull_picture",
}

key_mapping_about = {
    "id": "fb_page_id",
    "name": "fb_page_name",
    "link": "fb_page_url",
    "picture": "fb_page_picture",
    "cover": "fb_page_cover",
    "website": "fb_page_website",
    "phone": "fb_page_phone",
    "emails": "fb_page_emails",
    "contact_address": "fb_page_address",
    "page_created_time": "fb_page_created_time",
    "followers_count": "fb_page_followers_count",
    "fan_count": "fb_page_likes_count",
    "category": "fb_page_category"
}

class User_Functions():
    def __init__(self, includesPosts):
        self.includesPosts = includesPosts     

    def get_id(self,driver):
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        ele_text = soup.find(string=lambda text: text and 'userID' in text)
        text = ele_text
        pattern = r'userID'
        driver.implicitly_wait(5)
        matches = re.search(pattern, text)
        start, end = matches.span()
        text = text[end+3:]
        userID = text.split('"')[0]
        if userID:
            logging.info(f"Found id: {userID}")
        return userID  

    def fetch_user(self, url):
        response = requests.get(url)
        data = response.json()
        return data

    def get_friends(self, user_id, access_token):
        friends_list = []
       # url = f"{request_url_head}{user_id}?fields=friends%7Bname%2Cid%2Clink%7D&access_token={access_token}"
        url=f"{request_url_head}{user_id}/friends?access_token={access_token}&fields=id,name,link"
        while url:
            data = self.fetch_user(url)
            #next_url, friends = self.data_handling_friends(data)
            self.process_friends(data, friends_list)
            next_url = data.get('paging', {}).get('next', '')
            #if friends:
            #    friends_list.extend(friends)
            if next_url:
                url_parts = next_url.split('&')
                filtered_parts = [part for part in url_parts if not part.startswith('limit=')]
                url = '&'.join(filtered_parts)
            else:
                url = None
        return friends_list
    def process_friends(self,data, friends_list):
        friends = data.get('data', [])
        for friend in friends:
            friends_list.append({"fb_id": friend['id'], "fb_name": friend['name'],"fb_link" :friend['link']})
    # def data_handling_friends(self, data_dict):
    #     friends = data_dict.get('friends')
    #     if not friends:
    #         friends = data_dict.get('data')
    #     next_page = friends.get('paging', {})
    #     next_url = next_page.get('next')
    #     return next_url, friends

    def get_likes(self, user_id, access_token):
        likes_list = []
        #url = f"{request_url_head}{user_id}?fields=likes%7Bid%2Cname%2Clink%7D&access_token={access_token}"
        url=f"{request_url_head}{user_id}/likes?access_token={access_token}&fields=id,name,link"
        while url:
            data = self.fetch_user(url)
            likes = data.get('data', [])
            for like in likes:
                likes_list.append({"fb_id": like.get('id', ''), "fb_name": like.get('name', ''), "link": like.get('link', '')})
            next_url = data.get('paging', {}).get('next', '')
            if next_url:
                url_parts = next_url.split('&')
                filtered_parts = [part for part in url_parts if not part.startswith('limit=')]
                url = '&'.join(filtered_parts)
            else:
                url = None  
        return likes_list 

    # def data_handling_likes(self, data_dict):
    #     likes = data_dict.get('likes')
    #     if not likes:
    #         posts = data_dict.get('data')
    #     next_page = likes.get('paging', {})
    #     next_url = next_page.get('next')
    #     return next_url, posts

    def get_family(self, user_id, access_token):
        family_list = []
        request_url = f"{request_url_head}{user_id}/family?access_token={access_token}&fields=id,name,relationship&limit=15"
        response = requests.get(request_url)
        data = response.json()
        family_list = data['data']
        return family_list

    def get_about(self, user_id, access_token):
        fields = 'id,name,picture,location,work,education,relationship_status,events,email,mobile_phone,gender,birthday'
        request_url = f"{request_url_head}{user_id}?fields={fields}&access_token={access_token}"
        response = requests.get(request_url)
        profile = response.json()
        return profile

    def get_posts(self, user_id, access_token):
        request_url = f'{request_url_head}{user_id}?fields=id,posts%7Bcreated_time,message,full_picture,{reactions_count_field},comments.limit(25)%7Bid,created_time,from,message,attachment,comments.limit(25)%7Bid,created_time,from,message,attachment%7D%7D%7D&access_token={access_token}'
        response = requests.get(request_url)
        json_dict = response.json()
        posts = []
        next_url, posts = self.data_handling_posts(json_dict)
        prev_time = posts[0]['created_time']
        while next_url :
            response = requests.get(next_url)
            json_dict = response.json()
            next_url, next_posts = self.data_handling_posts(json_dict)
            if next_posts:
                next_time = next_posts[0]['created_time']
                if next_time != prev_time:
                    prev_time = next_time
                    posts.extend(next_posts)
                else:
                    break
            else:
                break
        post_dict = {
            'fb_id': user_id,
            'fb_posts': posts
        }
        post_dict = self.rename_keys_posts(post_dict, key_mapping)
        return post_dict

    def data_handling_posts(self, json_dict):
        posts_next = json_dict.get('posts', json_dict.get('feed'))
        if not posts_next:
            #posts = json_dict.get('data')
            return None,[]
        else:
            posts = posts_next.get('data')
        next_page = posts_next.get('paging', {})
        next_url = next_page.get('next')
        return next_url, posts

    def rename_keys_posts(self, obj, key_mapping, context=None):
        if isinstance(obj, dict):
            new_obj = {}
            for k, v in obj.items():
                new_key = key_mapping.get(k, k)
                if context == 'posts':
                    if k == 'message':
                        new_key = 'fb_pmessage'
                    elif k == 'id':
                        new_key = 'fb_pid'
                    elif k == 'created_time':
                        new_key = 'fb_pcreated_time'
                elif context == 'comments':
                    if k == 'message':
                        new_key = 'fb_cmessage'
                    elif k == 'id':
                        new_key = 'fb_cid'
                    elif k == 'created_time':
                        new_key = 'fb_ccreated_time'
                    elif k == 'comments':
                        new_key = 'fb_ccomments'
                elif context == 'reactions':
                    if k == 'name':
                        new_key = 'fb_name'
                    elif k == 'id':
                        new_key = 'fb_id'
                    elif k == 'type':
                        new_key = 'fb_rtype'
                elif context == 'from':
                    if k == 'name':
                        new_key = 'fb_name'
                    if k == 'id':
                        new_key = 'fb_id'
                if isinstance(v, (dict, list)):
                    new_obj[new_key] = self.rename_keys_posts(v, key_mapping, context=k)
                else:
                    new_obj[new_key] = v
            return new_obj
        elif isinstance(obj, list):
            return [self.rename_keys_posts(i, key_mapping, context=context) for i in obj]
        else:
            return obj

    def get_all_data(self, user_id, access_token):
        result = {}
        profile = self.get_about(user_id, access_token)
        result['fb_id'] = profile.get('id')
        result['fb_name'] = profile.get('name')
        result['fb_picture'] = profile.get('picture')
        result['fb_location'] = profile.get('location')
        result['fb_education'] = profile.get('education')
        result['fb_work'] = profile.get('work')
        result['fb_relationship_status'] = profile.get('relationship_status')
        result['fb_events'] = profile.get('events')
        result['fb_email'] = profile.get('email')
        result['fb_phone'] = profile.get('mobile_phone')
        result['fb_gender'] = profile.get('gender')
        result['fb_birthday'] = profile.get('birthday')
        result['fb_family'] = self.get_family(user_id, access_token)
        result['fb_friends'] = self.get_friends(user_id, access_token)
        result['fb_likes'] = self.get_likes(user_id, access_token)
        if self.includesPosts:
            posts_dict = self.get_posts(user_id, access_token)
            result.update(posts_dict)
        return result
