
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
#from webdriver_manager.chrome import ChromeDriverManager
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

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

logger.addHandler(console_handler)
key_mapping = key_mapping
key_mapping_about = key_mapping_about

class Functions:
    def get_page_id(self, driver, page_url, access_token):
        """Gets the ids of pages"""
        if ("?" in page_url):
            mark = '&'
        else:
            mark = "?"
        
        request_url = f'{request_url_head}{page_url}{mark}access_token={access_token}'
        
        driver.get(request_url)
        
        element = driver.find_element(By.TAG_NAME, "body")
        json_dict = json.loads(element.text)
                
        page_id = json_dict['id']
        return page_id
    def get_posts(self, driver, user_id, access_token):
        """Gets the posts of a page"""
        request_url = f'{request_url_head}{user_id}?fields=id%2Cposts%7Bcreated_time%2Cmessage%2Cfull_picture%2C{reactions_count_field}%2Ccomments.limit(25)%7Bid%2Cfrom%2Cmessage%2Ccomments.limit(25)%7D%7D&access_token={access_token}'
        # print(request_url)
        driver.get(request_url)
        element = driver.find_element(By.TAG_NAME, "body")

        json_dict = json.loads(element.text)

        posts = []

        next_url, posts = self.data_handling_posts(json_dict)
        try:
            page_id = json_dict['id']
        except KeyError:
            page_id = None

        
        prev_time = posts[0]['created_time']
        
        i = 0
        while(next_url and i < 10):
            driver.get(next_url)
            element = driver.find_element(By.TAG_NAME, "body")
            json_dict = json.loads(element.text)
            
            next_url, next_posts = self.data_handling_posts(json_dict)
            if next_posts:
                next_time = next_posts[0]['created_time']

                if next_time != prev_time:
                    prev_time = next_time
                    posts.extend(next_posts)
                else:
                    break  # Break the loop if no new posts are found
            else:
                break  # Break the loop if no new posts are found
        
        post_dict = {
            'fb_page_id': page_id,
            'fb_page_posts': posts
        }
        
        post_dict = self.rename_keys_posts(post_dict, key_mapping)
        
        return post_dict
    
    def data_handling_posts(self, json_dict):
        """
        Handles values inside the dict
        Goal: to get the posts list and URL to the next set of data
        """
        posts_next = json_dict.get('posts', json_dict.get('friends'))
    
        if not posts_next:
            # If neither 'comments' nor 'posts' is found, fallback to outer structure
            posts = json_dict.get('data')
            next_page = json_dict.get('paging', {})
        else:
            posts = posts_next.get('data')
            next_page = posts_next.get('paging', {})

        # Use get to retrieve 'next' URL
        next_url = next_page.get('next')

        return next_url, posts
    
    def rename_keys_posts(self, obj, key_mapping, context=None):
        """Function to rename keys from the posts dictionary"""
        if isinstance(obj, dict):
            new_obj = {}
            for k, v in obj.items():
                new_key = key_mapping.get(k, k)  # Default to original key
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
                    elif k =='comments':
                        new_key = 'fb_ccoments'
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

                # Set context for nested dictionaries
                if k == 'fb_page_posts':
                    new_context = 'posts'
                elif k == 'comments':
                    new_context = 'comments'
                elif k == 'reactions':
                    new_context = 'reactions'
                elif k == 'from':
                    new_context = 'from'
                else:
                    new_context = context

                new_obj[new_key] = self.rename_keys_posts(v, key_mapping, new_context)
            return new_obj
        elif isinstance(obj, list):
            return [self.rename_keys_posts(i, key_mapping, context) for i in obj]
        else:
            return obj
            
    def get_about(self, driver, user_id, access_token):
        """Gets the relevant fields from a page and store in a dictionary"""
        request_url = f'{request_url_head}{user_id}?fields=id%2Cname%2Clink%2Cpicture%7Burl%7D%2Ccover%7Bsource%7D%2Cabout%2Cwebsite%2Cphone%2Cemails%2Ccontact_address%2Cpage_created_time%2Cfollowers_count%2Cfan_count%2Ccategory&access_token={access_token}'
        response = requests.get(request_url)
        if response.status_code != 200:
            request_url=f'{request_url_head}{user_id}?fields=id%2Cname%2Clink%2Cpicture%7Burl%7D&access_token={access_token}'
        
        
        driver.get(request_url)
        element = driver.find_element(By.TAG_NAME, "body")
        json_dict = json.loads(element.text)
        
        json_dict = self.rename_keys_about(json_dict, key_mapping_about)

        return json_dict
    
    def rename_keys_about(self, obj, key_mapping, context=None):
        """Function to rename keys from the about dictionary"""
        if isinstance(obj, dict):
            new_obj = {}
            for k, v in obj.items():
                new_key = key_mapping.get(k, k)
                if context == 'picture':
                    if k == 'data':
                        context = 'data'
                        print('ok')
                elif context == 'data':
                    if k == 'url':
                        new_key = 'fb_picture_url'
                elif context == 'cover':
                    if k == 'source':
                        new_key = 'fb_cover_source'
                    elif k == 'id':
                        new_key = 'fb_cover_id'
                
                # Set context for nested dictionaries
                if k == 'picture':
                    new_context = 'picture'
                elif k == 'cover':
                    new_context = 'cover'
                else:
                    new_context = context
                    
                new_obj[new_key] = self.rename_keys_about(v, key_mapping, new_context)
            return new_obj
        elif isinstance(obj, list):
            return [self.rename_keys_about(i, key_mapping, context) for i in obj]
        else:
            return obj

    def get_all_data(self, driver, page_id, access_token):
        """Getting all data of one page (including the about and posts section)"""
        about_dict = self.get_about(driver, page_id, access_token)
        posts_dict = self.get_posts(driver, page_id, access_token)

        about_dict.update(posts_dict)
        
        output_dict = about_dict
        logger.info("Process done!")
        
        return output_dict   