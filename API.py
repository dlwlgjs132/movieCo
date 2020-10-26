from flask import Flask, jsonify, request
from lotte import LotteCinema
from cgv import Cgv
import ssl

app = Flask(__name__)
c = LotteCinema()
g = Cgv()

@app.route("/current-movie", methods=['GET'])
def get_current_movie():
    lotte_data = {}
    cgv_data = {}

    data = request.json
    latitude = data['latitude']
    longitude = data['longitude']

    lotte_data = c.get_current_movie(latitude, longitude)
    cgv_data = g.get_current_movie(latitude, longitude)

    lotte_data['CurrentMovieData'].extend(cgv_data['CgvCurrentMovieData'])
    return jsonify(lotte_data)

@app.route("/trailer", methods=['GET'])
def show_trailer():
    name_data = request.json
    print("name_data : ",name_data)
    movie_name = name_data['movie_name']
    
    return jsonify(c.show_trailer(movie_name))

@app.route("/specific-time-movie/<latitude>/<longitude>/<start>/<end>", methods=['GET', 'POST'])
def get_specific_time_movie(latitude,longitude,start, end=30):
    time_list = []
    if end == 30:
        time_list.append(start)
        return jsonify(c.get_specific_time_movie(latitude, longitude,time_list))
    
    time_list.append(start)
    time_list.append(end)

    lotte_data = {}
    cgv_data = {}

    lotte_data = c.get_specific_time_movie(latitude, longitude, time_list)
    cgv_data = g.get_specific_time_movie(latitude, longitude, time_list)

    lotte_data['SpecificTimeData'].extend(cgv_data['CgvSpecificTimeData'])
    return jsonify(lotte_data)

@app.route("/movie-name/<movie_name>/<latitude>/<longitude>", methods=['GET', 'POST'])    
def get_movie_name_theater(movie_name, latitude, longitude):
    return jsonify(c.get_movie_name_theater(latitude, longitude, movie_name))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
