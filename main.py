import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api import VkUpload
from random import randrange
from datetime import datetime
import requests


class Vkinder():
    host = '/home/andrey/py-team-diplom/'
    def __init__(self, id_partner=1):
        self.border = 1001
        if id_partner == 1:
            self.partner_id = self.get_number_cicle('partners_list.txt')
        else:
            self.partner_id = id_partner

    def get_token(self):
        with open(self.host + 'token_bot.txt') as f:
            token_bot = f.read().strip()
        return token_bot

    def get_service_token(self):
        with open(self.host + 'service_token.txt') as f:
            service_token = f.read().strip()
        return service_token

    def write_message(self, obj, user_id, message, attachments=[]):
        obj.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7), 'attachment': ','.join(attachments)})

    def get_user_data(self, obj, user_id):
        res = obj.method('users.get', {'user_id': user_id, 'v': '5.131', 'fields': 'sex, bdate, city, relation'})
        return res

    def output_users_info(self, obj, user_id):
        res = self.get_user_data(obj, user_id)
        profile_link = 'https://vk.com/id' + str(res[0]['id'])
        return '- {} {}\n- {}\n'.format(res[0]['first_name'], res[0]['last_name'], profile_link)
    
    def get_user_data_for_search(self, obj, user_id):
        res = self.get_user_data(obj, user_id)
        if 'is_closed' in res[0] and res[0]['is_closed'] or 'deactivated' in res[0] and (res[0]['deactivated'] == 'banned' or res[0]['deactivated'] == 'deleted'):
            return None
        if 'sex' in res[0]:
            gender = res[0]['sex']
        else:
            gender = 0
        if 'bdate' in res[0]:
            year = self.get_correct_year(res[0]['bdate'])
        else:
            year = ''
        if 'relation' in res[0]:
            if res[0]['relation'] in (1, 2, 5, 6, 7, 0):
                relation = 1
            else:
                relation = ''
        else:
            relation = 1
        if 'city' in res[0]:
            return (gender, year, res[0]['city']['title'], relation)
        else:
            return (gender, year, '', relation)

    def get_correct_year(self, bdate):
        if bdate.count('.') > 1:
            time_object = datetime.strptime(bdate, '%d.%m.%Y').year
        else:
            time_object = ''
        return time_object

    def send_sticker(self, obj, user_id, sticker_id):
        obj.method('messages.send', {'user_id': user_id, 'sticker_id': sticker_id,  'random_id': randrange(10 ** 7)})

    def get_photos(self, user_id):
        url = 'https://api.vk.com/method/photos.get'
        params = {'access_token': self.get_service_token(), 'v': '5.131', 'extended': 1, 'user_id': user_id, 'album_id': 'profile'}
        res = requests.get(url, params=params)
        if 'response' in res.json():
            items = res.json()['response']['items']
            return items
        return []
        
    def get_popular_photos(self, user_id):
        photos = self.get_photos(user_id)
        photo_ids_liked = []
        if photos:
            for photo in photos:
                photo_ids_liked.append((photo['id'], photo['likes']['count']))
            photo_ids_liked = sorted(photo_ids_liked, reverse=True, key=lambda x: x[1])
            ids_photo = [item[0] for item in photo_ids_liked[:3]]
            return ids_photo
        return []

    def get_photo_best_quality(self, photos):
        photo_urls = {}
        if photos:
            for photo in photos:
                photo_id = photo['id']
                dict_sizes = {}
                for image in photo['sizes']:
                    dict_sizes[image['type']] = image['url']
                for type_size in 'wzyxrqpmos':
                    if type_size in dict_sizes:
                        photo_urls[photo_id] = dict_sizes[type_size]
                        break
        return photo_urls

    def download_photo(self, url_image):
        if url_image:
            path = self.host + 'images/'
            if '?' in url_image:
                image_name = path + url_image.split('?')[0].split('/')[-1]
            else:
                image_name = path + url_image.split('/')[-1]
            res = requests.get(url_image, stream=True)
            with open(image_name, 'wb') as f:
                for chunk in res.iter_content():
                    f.write(chunk)
            return image_name
        return ''
        
    def download_photos(self, list_photos):
        list_images = []
        if list_photos:
            for url_photo in list_photos:
                image_name = self.download_photo(url_photo)
                list_images.append(image_name)
        return list_images
    
    def get_downloads_photos(self, user_id):
        list_popular_photos = self.get_popular_photos(user_id)
        dict_best_photos = self.get_photo_best_quality(self.get_photos(user_id))
        urls_photo = [value for key, value in dict_best_photos.items() if key in list_popular_photos]
        list_images = self.download_photos(urls_photo)
        return list_images

    def search_match_users(self, obj, user_id, num=1):
        list_images = ''
        human_info = self.get_user_data_for_search(obj, user_id)
        for partner_id in range(num, self.border):
            print(partner_id)
            if not self.get_user_data_for_search(obj, partner_id):
                continue
            partner_info = self.get_user_data_for_search(obj, partner_id)
            if 0 != partner_info[0] != human_info[0] != 0 and partner_info[2] == human_info[2] and partner_info[1] and human_info[1] and partner_info[3] and human_info[3]:
                if abs(partner_info[1] - human_info[1]) <= 5:
                    self.partner_id = partner_id
                    list_images = self.get_downloads_photos(partner_id)
            if list_images:
                return list_images
            
    def get_selected_people(self):
        with open(self.host + 'partners_list.txt', encoding='utf8') as f:
            list_ids = f.readlines()
        if list_ids:
            list_ids = ['https://vk.com/id' + item.strip() for item in list_ids]
            return ' '.join(list_ids)
        return 'Just empty'

    def get_number_cicle(self, filename):
        filename = self.host + filename
        with open(filename, 'r', encoding='utf8') as f:
            data_list = f.readlines()
        if not data_list:
            return 1
        return int(data_list[-1].strip())
    
    def record_id(self):
        with open(self.host + 'partners_list.txt', encoding='utf-8') as f:
            data_list = f.readlines()
        data_list = [item.strip() for item in data_list]
        with open(self.host + 'partners_list.txt', '+a', encoding='utf8') as f:
            if str(self.partner_id) not in data_list:
                f.write(str(self.partner_id) + '\n')

    
def launch():
    vkinder = Vkinder()
    vk_session = vk_api.VkApi(token=vkinder.get_token())
    longpoll = VkLongPoll(vk_session)
    upload = VkUpload(vk_session)
    list_greet = ['hello', 'hi', 'good morning', 'good afternoon', 'good evening']
    list_bye = ['goodbye', 'bye', 'good bye', 'bye bye']
    
    if vkinder.border < vkinder.partner_id:
        vkinder.border = vkinder.partner_id + 1000
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text
                if request == 'start':
                    number = vkinder.partner_id + 1
                    data_images = vkinder.search_match_users(vk_session, event.user_id, num=number)
                    while not data_images:
                        number, vkinder.border = vkinder.border, vkinder.border + 1000
                        data_images = vkinder.search_match_users(vk_session, event.user_id, num=number)
                    attachments = []
                    if data_images:
                        for image in data_images:
                            upload_image = upload.photo_messages(photos=image)[0]
                            attachments.append('photo{}_{}'.format(upload_image['owner_id'], upload_image['id']))
                    vkinder.write_message(vk_session, event.user_id, vkinder.output_users_info(vk_session, vkinder.partner_id), attachments)
                elif request == 'liked':
                    selected_users = vkinder.get_selected_people()
                    vkinder.write_message(vk_session, event.user_id, selected_users)
                elif request in list_greet:
                    vkinder.write_message(vk_session, event.user_id, f"Hi!")
                    vkinder.send_sticker(vk_session, event.user_id, 63)
                elif request in list_bye:
                    vkinder.write_message(vk_session, event.user_id, f"Bye bye")
                    vkinder.send_sticker(vk_session, event.user_id, 75)
                elif request == 'record':
                    vkinder.record_id()
                elif request == 'quit':
                    vkinder.write_message(vk_session, event.user_id, "Good luck!")
                    break
                

if __name__ == '__main__':
    launch()
