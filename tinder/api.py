import json
import requests
import datetime
from geopy.geocoders import Nominatim
from time import sleep
from random import random

import logging
logger_api = logging.getLogger('api')
logger_file = logging.getLogger('file')

TINDER_URL = "https://api.gotinder.com"
geolocator = Nominatim(user_agent="auto-tinder")
PROF_FILE = "./images/unclassified/profiles.txt"


class TinderAPI:
    def __init__(self, token):
        self._token = token

    def profile(self):
        """ Data contains only data part of the html file
            as far as super_data contains all information about customer.
            The reason that they are separated is to extract most of the useful
            information it is enough to have data
        """

        headers = {"X-Auth-Token": self._token}
        endpoint = "/v2/profile?include=account%2Cuser"
        response = requests.get(TINDER_URL + endpoint, headers=headers)

        if response.status_code == 200:
            data = response.json()['data']
            # TODO: what can I receive from super_data?
            super_data = requests.get(TINDER_URL + "/v2/profile?locale=en&include=account%2Cavailable_descriptors%"
                                                   "2Cboost%2Cbouncerbypass%2Ccontact_cards%2Cemail_settings%2Cinstagram%"
                                                   "2Clikes%2Cprofile_meter%2Cnotifications%2Cmisc_merchandising%"
                                                   "2Cofferings%2Cplus_control%2Cpurchase%2Creadreceipts%"
                                                   "2Cspotify%2Csuper_likes%2Ctinder_u%2Ctravel%2Ctutorials%2Cuser%2C",
                                      headers={"X-Auth-Token": self._token}).json()
            # print(f"super_data.keys: {super_data['data'].keys()}")
            # Q: could we receive super_data for free account?
            return {'meta': {'status': response.status_code}, 'data': {'profile': Profile(data, super_data, self)}}
            # return response.json()

        logger_file.error(dict(message=f"TOKEN: check freshness: status_code: {response.status_code}"))
        logger_api.error(f"TOKEN: check freshness: status_code: {response.status_code}")
        return {'meta': {'status': response.status_code}}


    def matches(self, limit=10):
        '''return list of t_user with whom is match. Every t_user is a sample of Person dataclass'''
        data = requests.get(TINDER_URL + f"/v2/matches?count={limit}", headers={"X-Auth-Token": self._token}).json()
        return list(map(lambda match: User(match["person"], match, self), data["data"]["matches"]))

    def number_of_likes(self):
        """ This function returns the number of people who already liked the account """
        data = requests.get(TINDER_URL + f"/v2/fast-match/count", headers={"X-Auth-Token": self._token}).json()
        return {"is_match": data["match"]}  #!?! what is data  without the key 'match' !?!

    def like(self, user_id):
        try:
            data = requests.get(TINDER_URL + f"/like/{user_id}", headers={"X-Auth-Token": self._token}).json()
            return {"is_match": data["match"]}
        except:
            # return relation = error
            pass

    ### !!! impliment skip !!! ### - research how many times the same people comming
    def skip(self, user_id):
        data = requests.get(TINDER_URL + f"/pass/{user_id}", headers={"X-Auth-Token": self._token}).json()
        return True

    def dislike(self, user_id):
        requests.get(TINDER_URL + f"/pass/{user_id}", headers={"X-Auth-Token": self._token}).json()
        return True

    def nearby_persons(self):
        ### !!! input timeout: if not respond after n seconds, then send request again !!! ###
        headers = {"X-Auth-Token": self._token}
        endpoint = "/v2/recs/core"
        response = requests.get(TINDER_URL + endpoint, headers=headers).json()
        return list(map(lambda user: User(user["user"], user, self), response["data"]["results"])), \
            response["data"]["results"]

    def get_person(self, user_id):
        response = requests.post(TINDER_URL + f"/user/{user_id}",
                                 headers={"X-Auth-Token": self._token})
        return response

    def get_self(self, s):
        """
        Returns your own profile data
        :param s:
        :return:
        """
        try:
            response = requests.get(TINDER_URL + f"/user/{s}", headers={"X-Auth-Token": self._token}).json()
            return response
        except requests.exceptions.RequestException as e:
            print("Something went wrong. Could not get your data:", e)

    # def send_message(self, user_id: int, message: str):
    #     data = requests.post(TINDER_URL + f"/user/matches/{user_id}", data=json.dumps({'message': message}),
    #                          headers={"X-Auth-Token": self._token})
    #     return data
    def send_message(self, message_text, match_id):
        #  match_id = {customer_id}{match_id}
        first_response = requests.post(TINDER_URL + f"/user/matches/{match_id}",
                                       data=json.dumps({"message": message_text}),
                                       headers={'x-auth-token': self._token,
                                                'Content-Type': 'application/json'})

        # second_response = requests.post(TINDER_URL + f"/user/matches/{match_id}{customer_id}",
        #                                 data=json.dumps({"message": message_text}),
        #                                 headers={'x-auth-token': self._token,
        #                                          'Content-Type': 'application/json'})
        # if (first_response.status_code != 200) and (second_response.status_code != 200):
        #     return first_response
        return "Message sent successfully"

    def get_message_matches_hist(self, last_activity_date: str) -> json:
        """
        Returns json data of profile updates since <last_activity_date>
        :param last_activity_date: to receive user data for all time = ""
        :param last_activity_date: format: "2023-01-18T07:56:24.332Z"
        """

        raw_data = requests.post(TINDER_URL + "/updates?locale=en",
                                 json={"last_activity_date": f"{last_activity_date}"},
                                 headers={"X-Auth-Token": self._token}).json()
        return raw_data

    def reset_job(self):
        return requests.delete(TINDER_URL + f"/profile/job", headers={"X-Auth-Token": self._token}).json()

    def unmatch(self, match_id):
        return requests.post(TINDER_URL + f"/user/matches/{match_id}", headers={"X-Auth-Token": self._token}).json()


class User(object):
    """ This function is representor of both customer and user.
        So it has common attributes between both of them
    """

    def __init__(self, user, data, api):
        self._api = api

        self.id = user["_id"]
        self.name = user.get("name", "Unknown")
        self.bio = user.get("bio", '')
        ### !!! leave only yearch without month as dayt ans month is not right for t_users - check it !!! ###
        self.birth_date = datetime.datetime.strptime(user["birth_date"], '%Y-%m-%dT%H:%M:%S.%fZ') if user.get(
            "birth_date", False) else ''
        ### !!! search in html 'near by person', WHAT is 'distance_mi' ? !!! ###
        self.distance = data.get("distance_mi", '')

        # TODO: store only numbers, not names, as tinder can make changes and create other genders
        self.gender = ["Male", "Female", "Unknown"][user.get("gender", 2)]
        self.images = list(map(lambda photo: photo["url"], user.get("photos", '')))

        self.job_title = ", ".join(map(lambda job: job.get("title", {}).get("name", ''), user.get("jobs", '')))
        self.company = ", ".join(map(lambda job: job.get("company", {}).get("name", ''), user.get("jobs", '')))

        self.schools = ", ".join(map(lambda school: school["name"], user.get("schools", '')))
        self.__name_of_selected_descriptors = list(
            map(lambda descriptor: descriptor.get("name", ''), user.get("selected_descriptors", ''))
        )
        self.__choice_selections_of_selected_descriptors = list(
            map(lambda descriptor: descriptor.get("choice_selections", ''), user.get("selected_descriptors", ''))
        )
        self.smoke_status = \
            self.__choice_selections_of_selected_descriptors[self.__name_of_selected_descriptors.index("Smoking")][0][
                "name"] if (self.__name_of_selected_descriptors.__contains__("Smoking")) else ''
        self.zodiac_status = \
            self.__choice_selections_of_selected_descriptors[self.__name_of_selected_descriptors.index("Zodiac")][0][
                "name"] if (self.__name_of_selected_descriptors.__contains__("Zodiac")) else ''
        self.pets_status = \
            self.__choice_selections_of_selected_descriptors[self.__name_of_selected_descriptors.index("Pets")][0][
                "name"] if (self.__name_of_selected_descriptors.__contains__("Pets")) else ''
        self.sexual_orientation = ", ".join(
            map(str, list(map(lambda s_o: s_o["name"], user.get("sexual_orientations", '')))))

        self.passions = ", ".join(map(lambda interest: interest["name"], data["experiment_info"]["user_interests"][
            "selected_interests"])) if "experiment_info" in data.keys() else ''

        if "facebook" in data:
            self.facebook_common_connections = data["facebook"].get("common_connections", "")
            self.facebook_connection_count = data["facebook"].get("connection_count", "")
            self.facebook_common_interests = data["facebook"].get("connection_count", "")

        if "spotify" in data:
            if 'spotify_theme_track' in data['spotify']:
                theme_track = data['spotify']['spotify_theme_track']
                self.theme_song_name = theme_track.get('name', "")
                self.theme_album_name = theme_track['album'].get('name', "")
                self.theme_artists = {artist_name.get('name', "") for artist_name in theme_track['artists']}
            else:
                self.theme_song_name = ""
                self.theme_album_name = ""
                self.theme_artists = ""

            if "spotify_top_artists" in data["spotify"]:
                    artists = set()
                    songs_album = dict()

                    for item in data['spotify']['spotify_top_artists']:
                        top_track = item['top_track']
                        if top_track is not None:
                            song_name = top_track['name']
                            songs_album[song_name] = top_track['album']['name']
                            artists |= {artist_name['name'] for artist_name in top_track['artists']}

                    self.artists = artists if bool(artists) is True else ""
                    self.songs_album = songs_album if bool(songs_album) is True else ""

            else:
                self.artists = ""
                self.songs_album = ""

        self.type_account = data["type"] if "type" in data else ''
        self.city = user["city"]["name"] if "city" in user else ''
        self.s_number = data.get("s_number", '')

        # work only for profiles with known token
        if user.get("pos", False):
            self.location = geolocator.reverse(f'{user["pos"]["lat"]}, {user["pos"]["lon"]}')

    def __repr__(self):
        return f"{self.id}  -  {self.name} ({self.birth_date})"

    def like(self):
        return "liked", self._api.like(self.id)

    def dislike(self):
        return "dislike", self._api.dislike(self.id)

    def download_images(self, tinder_image_id: str, folder=".", sleep_max_for=0):
        # TODO: implement the next paradigm to downloading (working with DB.tin_Users.data_collection)
        f"https://images-ssl.gotinder.com/{self.id}/original_{tinder_image_id}.jpeg"  # ...

        with open(PROF_FILE, "r") as f:

            lines = f.readlines()
            if self.id in lines:
                return
        with open(PROF_FILE, "a") as f:
            f.write(self.id + "\r\n")
        index = -1
        for image_url in self.images:
            index += 1
            req = requests.get(image_url, stream=True)
            if req.status_code == 200:
                with open(f"{folder}/{self.id}_{self.name}_{index}.jpeg", "wb") as f:
                    f.write(req.content)
            sleep(random() * sleep_max_for)


class Profile(User):

    def __init__(self, data, super_data, api):
        super().__init__(data["user"], data, api)

        self.cust_adds = None  # it will be filled after
        self.email = data["account"].get("account_email")
        self.phone_number = data["account"].get("account_phone_number")
        self.age_min = data["user"]["age_filter_min"]
        self.age_max = data["user"]["age_filter_max"]
        self.max_distance = data["user"]["distance_filter"]
        self.gender_filter = ["Male", "Female"][data["user"]["gender_filter"]]
        if "spotify_theme_track" in super_data["data"]["spotify"]:
            self.song_name = super_data["data"]["spotify"]["spotify_theme_track"]["name"]
            self.musics_artist = super_data["data"]["spotify"]["spotify_theme_track"]["artists"][0]["name"]
        else:
            self.song_name = ""
            self.musics_artist = ""

        if "city" in data["user"]:
            ### !!! bring all to view:  get(..., ''), as more compact  and it possiblee many variants
            ### self.song_name = ", ".join(map(lambda job: job.get("title", {}).get("name"), user.get("jobs", ''))) !!! ###
            self.country = data["user"]["city"]["region"] if "city" in data["user"] else ""
            self.city = data["user"]["city"]["name"]
        else:
            self.country = ""
            self.city = ""
        self.instagram = super_data["data"]["instagram"]
        self.username = data["user"]["username"] if "username" in data["user"] else ""
        self.passions = ", ".join(map(str, list(
            map(lambda interest: interest["name"], data["user"]["user_interests"]["selected_interests"]))))
        self.available_passions = ", ".join(map(str, list(
            map(lambda interest: interest["name"], data["user"]["user_interests"]["available_interests"]))))

        self.language_preferences = ""
        if "global_mode" in data["user"]:
            if "language_preferences" in data["user"]["global_mode"]:
                self.language_preferences = data["user"]["global_mode"]["language_preferences"]

        self.sd = super_data  # This is temporary ( for getting all information and processing it)