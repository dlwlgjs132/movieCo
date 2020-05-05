import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd
import math
from datetime import datetime

class Cgv(object):
    def get_near_theater(self, current_latitude, current_longitude):
        df = pd.read_csv('./seoul_cgv.csv')
    
        distance_list = []
        distance_idx_list = []
        for i in range(len(df)):
            latitude = df['위도'][i]
            longitude = df['경도'][i]
            
            distance = self.get_distance(latitude, longitude, current_latitude, current_longitude)

            if distance <= 5:
                distance_idx_list.append(i)
                distance_list.append(distance)
        
        return_data_list = []
        
        
        for n, i in enumerate(distance_idx_list):
            data_dict = {}
            theater_dict = {}
            data_dict['Name'] = df['사업장명'][i]
            data_dict['Latitude'] = df['위도'][i]
            data_dict['Longitude'] = df['경도'][i]
            data_dict['TheaterCode'] = df['코드명'][i]
            data_dict['Distance'] = str(round(distance_list[n], 2))+'km'
            
            theater_dict['Theater'] = data_dict
            return_data_list.append(theater_dict)
        
        return return_data_list
        
    def get_distance(self, latitude, longitude, current_latitude, current_longitude):
        to_radian = math.pi/180

        latitude = float(latitude)
        longitude = float(longitude)
        current_latitude = float(current_latitude)
        current_longitude = float(current_longitude)

        theta = abs(longitude - current_longitude)
        dist = math.sin((latitude * to_radian)) * math.sin((current_latitude*to_radian))+ math.cos((latitude * to_radian)) * math.cos((current_latitude * to_radian)) * math.cos((theta * to_radian))
        
        dist = math.acos(dist)
        dist = dist * (180 / math.pi)
        dist = dist * 60 * 1.1515 * 1.609344
        return dist

    def get_current_movie(self, current_latitude, current_longitude):
        near_theater_list = self.get_near_theater(current_latitude, current_longitude)
    
        return_data_list = []
        for near_theater in near_theater_list:
            url = 'http://www.cgv.co.kr/common/showtimes/iframeTheater.aspx?'
            code = near_theater['Theater']['TheaterCode']
            date = '&date=20200121'
            
            url = url + code + date
            request = requests.get(url)
            
            html = request.text
            soup = BeautifulSoup(html, 'html.parser')
            
            movie_data_list = soup.select('body > div > div.sect-showtimes > ul > li > div')
            movie_data_dict = {}
            
            movie_data_all_dict = {}

            for movie_data in movie_data_list:
                movie_name_list = movie_data.select('div.info-movie > a > strong')
                # 영화별 시간알려주기
                movie_time_seat_list = movie_data.select('div.type-hall > div.info-timetable > ul > li > a')    

                time_seat_dict = {}
                time_seat_list = []
                for mtsl in movie_time_seat_list:
                    tmp_list = []
                    tmp = mtsl.text.split('잔여좌석')

                    # 현재 시간을 나타낸다.
                    target_dt = datetime.now()
                    target_dt_str = target_dt.strftime('%H')

                    current_time = target_dt_str
                    tmp_time = tmp[0]
                    tmp_time = int(tmp_time[0:2])

                    if int(current_time) <= tmp_time and tmp_time <= (int(current_time) + 1):
                        tmp_list.append(tmp[0])
                        tmp_list.append(tmp[1])
                        time_seat_list.append(tmp_list)

                # 영화이름 알려주기
                for mn in movie_name_list:
                    if len(time_seat_list) != 0:
                        movie_data_dict[mn.text.strip()] = time_seat_list
            
            near_theater['Movie'] = movie_data_dict

            return_data_list.append(near_theater)
            
        return {'CgvCurrentMovieData':return_data_list}

    def get_specific_time_movie(self, current_latitude, current_longitude, time):
        #time은 2개를 가진 리스트
        near_theater_list = self.get_near_theater(current_latitude, current_longitude)
        
        return_data_list = []
        for near_theater in near_theater_list:
            # near_theater은 dict 형식('Theater'이 key인 형식)
            url = 'http://www.cgv.co.kr/common/showtimes/iframeTheater.aspx?'
            code = near_theater['Theater']['TheaterCode']
            date = '&date=20200121' # 변수로 넣어도됨
            
            url = url + code + date
            request = requests.get(url)
            
            html = request.text
            soup = BeautifulSoup(html, 'html.parser')
            
            movie_data_list = soup.select('body > div > div.sect-showtimes > ul > li > div')
            movie_data_dict = {}
            
            movie_data_all_dict = {}

            for movie_data in movie_data_list:
                movie_name_list = movie_data.select('div.info-movie > a > strong')
                # 영화별 시간알려주기
                movie_time_seat_list = movie_data.select('div.type-hall > div.info-timetable > ul > li > a')    

                time_seat_dict = {}
                time_seat_list = []
                for mtsl in movie_time_seat_list:
                    tmp_list = []
                    tmp = mtsl.text.split('잔여좌석')

                    
                    target1 = int(time[0])
                    target2 = int(time[1])
                    
                    tmp_time = tmp[0]
                    tmp_time = int(tmp_time[0:2])

                    if target1 <= tmp_time and tmp_time < target2:
                        tmp_list.append(tmp[0])
                        tmp_list.append(tmp[1])
                        time_seat_list.append(tmp_list)

                # 영화이름 알려주기
                for mn in movie_name_list:
                    if len(time_seat_list) != 0:
                        movie_data_dict[mn.text.strip()] = time_seat_list
            
            near_theater['Movie'] = movie_data_dict

            return_data_list.append(near_theater)
            

            
        return {'CgvSpecificTimeData':return_data_list}