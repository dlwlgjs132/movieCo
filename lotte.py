import json
import math
from datetime import datetime
from urllib.request import urlopen
from urllib.parse import urlencode
import numpy as np

class LotteCinema(object):
    lotte_url = 'http://www.lottecinema.co.kr'
    lotte_url_cinema_data = '{}/LCWS/Cinema/CinemaData.aspx'.format(lotte_url)
    lotte_url_movie_list = '{}/LCWS/Ticketing/TicketingData.aspx'.format(lotte_url)
    
    # 데이터 가져오기위해 변환하는 함수들
    def make_payload(self, **kwargs):
        param_list = {'channelType': 'MW', 'osType': '', 'osVersion': '', **kwargs}
        data = {'ParamList': json.dumps(param_list)}
        payload = urlencode(data).encode('utf8')
        return payload

    def json_to_byte(self, fp):
        content = fp.read().decode('utf8')
        # python에서 바로 데이터 접근 가능(str을 dict로 변환)
        return json.loads(content)
        
    # 영화관 정보 가져오기
    # 영화관 이름, 영화관 ID, 위도, 경도 정보를 가져올 수 있다.
    def get_theater_list(self):
        url = self.lotte_url_cinema_data
        # 영화관 페이지로 들어가면 볼 수 있다.
        payload = self.make_payload(MethodName='GetCinemaItems')
        with urlopen(url, data=payload) as fin:
            json_content = self.json_to_byte(fin)
            # 리스트안에 dict형태로 반환
            return [
                {
                    'TheaterName': '{} 롯데시네마'.format(entry.get('CinemaNameKR')),
                    'TheaterID': '{}|{}|{}'.format(entry.get('DivisionCode'), entry.get('SortSequence'), entry.get('CinemaID')),
                    'Longitude': entry.get('Longitude'),
                    'Latitude': entry.get('Latitude')
                }
                for entry in json_content.get('Cinemas').get('Items')
            ]
    
    # 영화 정보 가져오기
    # 영화이름, 좌석수, 시작 시간 정보를 가져올 수 있다.
    # 반환형태를 {'영화 코드' : {'Name' : '영화이름', 
    #                      'Schedules' : [{'StartTime':'시간',
#                             'RemainingSeat' : '남은자리'}]},
#               '영화 코드' : {...}}
    # 나중에 정보가 필요하면 values값을 가져다가 쓴다.
    def get_movie_list(self, theater_id):
        url = self.lotte_url_movie_list
        # 나중에 시간 바꾼 것을 하고 싶으면 밑에거를 바꾸면된다.
        target_dt = datetime.now()
        target_dt_str = target_dt.strftime('%Y-%m-%d')
        # 사이트에서 관리자모드로 들어가서 TicketingData.aspx 부분을 보게되면
        # 거기서 요청부분을 보면 된다.
        payload = self.make_payload(MethodName='GetPlaySequence', playDate=target_dt_str, cinemaID=theater_id, representationMovieCode='')
        with urlopen(url, data=payload) as fin:
            json_content = self.json_to_byte(fin)
            movie_id_to_info = {}
            # get을 하게되면 json형태에서 가져온다.
            for entry in json_content.get('PlaySeqsHeader', {}).get('Items', []):
                movie_id_to_info.setdefault(entry.get('MovieCode'), {})['Name'] = entry.get('MovieNameKR')

            for order, entry in enumerate(json_content.get('PlaySeqs').get('Items')):
                schedules = movie_id_to_info[entry.get('MovieCode')].setdefault('Schedules', [])
                schedule = {
                    'StartTime': '{}'.format(entry.get('StartTime')),
                    'RemainingSeat': int(entry.get('BookingSeatCount'))
                }
                schedules.append(schedule)
            return movie_id_to_info
    # 거리계산
    # 거리 구하는 공식 => km로 가져온다.
    def distance(self, latitude, longitude, current_latitude, current_longitude):
        to_radian = math.pi/180
#         print(type(longitude), type(current_longitude))
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
#     def distance(self, x1, x2, y1, y2):
#         dx = float(x1) - float(x2)
#         dy = float(y1) - float(y2)
#         distance = math.sqrt(dx**2 + dy**2)
#         return distance
    # (영화관 리스트, 위도, 경도, 몇개의 영화관 불러올지)
    # 반환 값으로 영화관의 정보가 반환된다.
    def filter_nearest_theater(self, theater_list, pos_latitude, pos_longitude, n=5):
        distance_to_theater = []

        distance_idx_list = []
        for theater in theater_list:
#             print(theater)
            distance_list = []
            distance = self.distance(pos_latitude, pos_longitude,theater.get('Latitude'), theater.get('Longitude'))
            if distance <= 3:
                distance_list.append(theater)
                distance_list.append(round(distance, 2))
#                 distance_idx_list.append(theater)
#                 distance_list.append(distance)
                distance_to_theater.append(distance_list)
        
# [theater for distance, theater in sorted(distance_to_theater, key=lambda x: x[0])[:n]]
        # 반환값 : 각 영화관 마다의 거리
        # theater : dist
        return distance_to_theater

    # 현재 가장 가까운 영화관 알려줘
    # 인자로 현재 위도, 경도 값을 받는다.
    # output : 영화관(위도와 경도?(지도를 보여줘야할 수도 있어서), 업체 => 보류)
#     def get_near_theater(self, current_latitude, current_longitude):
#         theater_list = self.get_theater_list()
#         near_theater = self.filter_nearest_theater(theater_list, current_latitude, current_longitude)
        
#         return [theater for theater in near_theater['Theeatername']]

    # (지금) 볼 수 있는 영화 있어?
#   - input : 현재위치
#   - output : 영화명, 시간, 좌석수, 영화관, 업체->나중에 추가(현재시간에서 +1시간 정도까지만 영화정보제공) 
    def get_current_movie(self, current_latitude, current_longitude):
        # 영화관 5개 -> 1시간 내의 영화(시간기준) -> 영화명, 시간저장
        # 영화관 5개 정보 가져오기
        theater_list = self.get_theater_list()
        near_theater = self.filter_nearest_theater(theater_list, current_latitude, current_longitude)
#         print(near_theater)
        theater_distance = [distance[1] for distance in near_theater]
#         print(near_theater[0])
        near_theater = [n[0] for n in near_theater]
        near_theater_name = [name['TheaterName'] for name in near_theater]
        near_theater_ID = [ID['TheaterID'] for ID in near_theater]
        theater_longitude = [pos['Longitude'] for pos in near_theater]
        theater_latitude = [pos['Latitude'] for pos in near_theater]
        # 1시간 내의 영화 찾기
        # 영화관마다 영화 다 돌면서 1시간내에 있는 정보를 가져온다.
        theaters_data = []
        
        # 근처 5개 영화관에서 정보 찾기
        for i, theater_ID in enumerate(near_theater_ID):
            movie_id_to_info = self.get_movie_list(theater_ID)
            target_dt = datetime.now()
            target_dt_str = target_dt.strftime('%H')
            # 영화관, 영화 : [시간들]
            # [{'Theater' : '영화관 이름',
            #  'Movie' : {'영화이름' : [시간들], ...}}]
            movie_schedules = {}
            # 영화관 별 영화마다 시간비교해서 정보찾기
            for info in movie_id_to_info.values():
                movie_times = []
                movie_schedules_list = []
                movie_times_dict = {}
                movie_name = info['Name']
                # 영화별 시간
                for schedule in info['Schedules']:
                    remaining_seat = schedule['RemainingSeat']
                    movie_times_list = []

                    in_time = int(schedule['StartTime'][0:2])
                    target_dt_int = int(target_dt_str)#
                    if in_time == target_dt_int or in_time == target_dt_int + 1:
#                         movie_times_dict[schedule['StartTime']] = remaining_seat
                        movie_times_list.append(schedule['StartTime'])
                        movie_times_list.append(remaining_seat)
                        movie_schedules_list.append(movie_times_list)

#                         movie_times.append(schedule['StartTime'])
                # 영화시간이 존재하면 더하기        
                if len(movie_schedules_list) != 0:
                    movie_schedules[movie_name] = movie_schedules_list
                
            
            # 'Movie' : {}
            # movie_schedules가 있으면
            theater_data = {}
            theater_body_data = {}
            if len(movie_schedules) != 0:
                theater_body_data['Name'] = near_theater_name[i]
                theater_body_data['Longitude'] = theater_longitude[i] 
                theater_body_data['Latitude'] = theater_latitude[i]
                theater_body_data['Distance'] = theater_distance[i]
                
                theater_data['Movie'] = movie_schedules
                theater_data['Theater'] = theater_body_data
                theaters_data.append(theater_data)
        
        return {'CurrentMovieData' : theaters_data}
        
# - Input : 원하는 시간(일단 시간이 1 or 2개로 들어올 수 도 있다. 그래서 시간을 순서대로 들어오게 하고 배열형태로), 현재 위치
# - output : 영화명, 시간, 좌석수, 영화관, 업체(해당 시간 안에 시작하는 영화반환), 위치
# - 함수명 : get_specific_time_movie
# time 인자는 리스트로(1개또는 2개의 시간이 들어올 수 있기 때문에)
    def get_specific_time_movie(self, current_latitude, current_longitude, time):
#         theater_list = self.get_theater_list()
#         near_theater = self.filter_nearest_theater(theater_list, current_latitude, current_longitude)
#         near_theater_name = [name['TheaterName'] for name in near_theater]
#         near_theater_ID = [ID['TheaterID'] for ID in near_theater]
#         theater_longitude = [pos['Longitude'] for pos in near_theater]
#         theater_latitude = [pos['Latitude'] for pos in near_theater]
        theater_list = self.get_theater_list()
        near_theater = self.filter_nearest_theater(theater_list, current_latitude, current_longitude)
#         print(near_theater)
        theater_distance = [distance[1] for distance in near_theater]
#         print(near_theater[0])
        near_theater = [n[0] for n in near_theater]

        near_theater_name = [name['TheaterName'] for name in near_theater]
        near_theater_ID = [ID['TheaterID'] for ID in near_theater]
        theater_longitude = [pos['Longitude'] for pos in near_theater]
        theater_latitude = [pos['Latitude'] for pos in near_theater]
        # 1시간 내의 영화 찾기
        # 영화관마다 영화 다 돌면서 1시간내에 있는 정보를 가져온다.
        theaters_data = []
        
        # 근처 5개 영화관에서 정보 찾기
        for i, theater_ID in enumerate(near_theater_ID):
            movie_id_to_info = self.get_movie_list(theater_ID)
            # 1 or 2개가 올 수 있다.
            # 문자열로 받기 ex) ['13', '15']
#             target_dt = time
#             target_dt_str = target_dt.strftime('%H')
            # 영화관, 영화 : [시간들]
            # [{'Theater' : '영화관 이름',
            #  'Movie' : {'영화이름' : [시간들], ...}}]
            movie_schedules = {}
            movie_schedules_list = []
            # 영화관 별 영화마다 시간비교해서 정보찾기
            for info in movie_id_to_info.values():
                movie_times = []
                movie_times_dict = {}
                movie_name = info['Name']
                # 영화별 시간
                for schedule in info['Schedules']:
                    remaining_seat = schedule['RemainingSeat']
                    in_time = int(schedule['StartTime'][0:2])
                    movie_times_list = []

                    if len(time) == 1:
                        target_dt_int = int(time[0])
                        if in_time >= target_dt_int:
                            movie_times_dict[schedule['StartTime']] = remaining_seat
#                             movie_times.append(schedule['StartTime'])
                    elif len(time) == 2:
                        target1 = int(time[0])
                        target2 = int(time[1])
                        if target1 <= in_time and in_time < target2:
                            movie_times_list.append(schedule['StartTime'])
                            movie_times_list.append(remaining_seat)
                            movie_schedules_list.append(movie_times_list)
#                             movie_times_dict[schedule['StartTime']] = remaining_seat
#                             movie_times.append(schedule['StartTime'])
                    
                # 영화시간이 존재하면 더하기        
                if len(movie_schedules_list) != 0:
                    movie_schedules[movie_name] = movie_schedules_list
            
            # 'Movie' : {}
            # movie_schedules가 있으면
            theater_data = {}
            theater_body_data = {}
            if len(movie_schedules) != 0:
#                 print(near_theater_name[i])
                theater_body_data['Name'] = near_theater_name[i]
                theater_body_data['Longitude'] = theater_longitude[i] 
                theater_body_data['Latitude'] = theater_latitude[i]
                theater_body_data['Distance'] = theater_distance[i]

                theater_data['Movie'] = movie_schedules
                theater_data['Theater'] = theater_body_data
                theaters_data.append(theater_data)
#                 theater_data['Movie'] = movie_schedules
                
#                 theater_body_data['Name'] = near_theater_name[i]
# #                 theater_body_data['Position'] = 
#                 theater_data['Theater'] = near_theater_name[i]
#                 theaters_data.append(theater_data)
        
        return {'SpecificTimeData' : theaters_data}
        
# #   (영화이름) 예고편 보여줘
# - Input : 영화이름
# - output : 링크 주소
# - 함수명 : show_trailer
    def show_trailer(self, movie_name):
        url = self.lotte_url_movie_list
        
        payload = self.make_payload(MethodName='GetTicketingPageTOBE', memberOnNo='0')
        
        trailer_url = ""
        with urlopen(url, data=payload) as fin:
            json_content = self.json_to_byte(fin)

            for entry in json_content.get('Movies').get('Movies').get('Items'):
                if entry['MovieNameKR'] == movie_name:
                    trailer_url = entry['PosterURL']
                    break
            # 예고편이 없는 경우는 ""가 반환되고 js쪽에서 처리한다.
            
            return_url = trailer_url.replace('_201', '_301').replace('.jpg', '.mp4').replace('MovieImg', 'MovieMedia')
            return {'TrailerURL' : return_url}
        
# (영화이름) 볼 수 있는 영화관이 어디야?
# - Input : 현재 위치, 영화이름
# - output : 시간, 좌석수, 현재위치에서 가까운 5개 영화관, 위치, 업체
# - 함수명 : get_movie_name_theater
    def get_movie_name_theater(self, current_latitude, current_longitude, movie_name):
        url = self.lotte_url_movie_list
        theater_list = self.get_theater_list()
        # 가까운 거리에 있는거 받고 -> 순서대로 영화있는지 확인 -> 5개의 영화관 채워지면 return

        near_theater = self.filter_nearest_theater(theater_list, current_latitude, current_longitude)
        theater_distance = [distance[1] for distance in near_theater]
        nearest_theater_list = [n[0] for n in near_theater]

        # 순서대로 영화있는지 확인
        # nearest_theater_list['TheaterID'] 반복문 돌면서 확인
        # get_movie_list(영화관 id)에서 영화관에 영화가 있는지 확인
        theater_info_list = []
        idx = 0
        for theater in nearest_theater_list:
            theater_movie_dict = {}
            movie_data = self.get_movie_list(theater['TheaterID'])
            for name in movie_data.values():
                if name['Name'] == movie_name:
                    movie_info = {}
                    movie_data_list = []
                    for schedule in name['Schedules']:
                        movie_info_list = []
                        movie_info_list.append(schedule['StartTime'])
                        movie_info_list.append(schedule['RemainingSeat'])
                        movie_data_list.append(movie_info_list)

                    theater_movie_dict['Movie'] = movie_data_list
                    
                    theater_longitude = theater['Longitude']
                    theater_latitude = theater['Latitude']
                    theater_dict = {}
                    theater_dict['Name'] = theater['TheaterName']
                    theater_dict['Longitude'] = theater_longitude
                    theater_dict['Latitude'] = theater_latitude
                    theater_dict['Distance'] = theater_distance[idx]
                    idx += 1
                    
                    theater_movie_dict['Theater'] = theater_dict
                    theater_info_list.append(theater_movie_dict)
                    break
            
            
            if len(theater_info_list) == 5:
                break
                
        return {"SearchMovieName" : theater_info_list}

# c.get_movie_name_theater(37.5, 126.844, "해치지않아")
# c.get_movie_name_theater(37.5, 126.844,'기생충')


