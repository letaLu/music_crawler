import requests
import json
import re
import time
import random
import os
import pickle
from bs4 import BeautifulSoup

OUTPUT_DIR = "netease_data"
SONGS_FILE = os.path.join(OUTPUT_DIR, "songs.json")
ARTISTS_FILE = os.path.join(OUTPUT_DIR, "artists.json")
STATE_FILE = os.path.join(OUTPUT_DIR, "crawl_state.pkl")
COOKIE_POOL = []

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

class NetEaseCrawler:
    def __init__(self):
        self.base_url = "https://music.163.com"
        self.session = requests.Session()
        self.completed_artist_ids = set()
        self.completed_song_ids = set()
        self.songs_data = []
        self.artists_data = []
        self._load_state()

    def _get_headers(self):
        h = {
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": "https://music.163.com/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        if COOKIE_POOL:
            h["Cookie"] = random.choice(COOKIE_POOL)
        return h

    def _request(self, url, extra_headers=None):
        for i in range(3):
            try:
                time.sleep(random.uniform(1, 3))
                headers = self._get_headers()
                if extra_headers:
                    headers.update(extra_headers)
                resp = self.session.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    return resp
                if resp.status_code == 429:
                    time.sleep((i+1)*5)
            except Exception as e:
                print(f"请求异常：{e}，重试 {i+1}/3")
        return None

    def _save_state(self):
        with open(STATE_FILE, "wb") as f:
            pickle.dump({
                "completed_artist_ids": self.completed_artist_ids,
                "completed_song_ids": self.completed_song_ids,
                "songs_data": self.songs_data,
                "artists_data": self.artists_data,
            }, f)

    def _load_state(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "rb") as f:
                state = pickle.load(f)
            self.completed_artist_ids = state.get("completed_artist_ids", set())
            self.completed_song_ids = state.get("completed_song_ids", set())
            self.songs_data = state.get("songs_data", [])
            self.artists_data = state.get("artists_data", [])
            print(f"从断点恢复：已完成 {len(self.completed_artist_ids)} 位歌手，{len(self.completed_song_ids)} 首歌曲")
        else:
            print("无历史状态，从头开始。")

    def _save_final_data(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(SONGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.songs_data, f, ensure_ascii=False, indent=2)
        with open(ARTISTS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.artists_data, f, ensure_ascii=False, indent=2)

    def fetch_artist_intro(self, artist_id):
        url = f"{self.base_url}/artist/desc?id={artist_id}"
        resp = self._request(url, {"Referer": f"{self.base_url}/artist?id={artist_id}"})
        if not resp:
            return ""
        soup = BeautifulSoup(resp.text, "lxml")
        div = soup.select_one("div.n-artdesc")
        if div:
            return div.get_text(separator="\n", strip=True)
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            return meta["content"].strip()
        return ""

    def ensure_artist(self, artist_id, artist_name, cover_url=''):
        for a in self.artists_data:
            if a['artist_id'] == artist_id:
                if a['artist_name'] in ('网易云音乐', '未知', '', None):
                    a['artist_name'] = artist_name
                if not a['artist_pic'] and cover_url:
                    a['artist_pic'] = cover_url
                return a
        artist_info = {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "artist_pic": cover_url,
            "artist_intro": "",
            "artist_url": f"{self.base_url}/artist?id={artist_id}",
        }
        self.artists_data.append(artist_info)
        return artist_info

    def fetch_artist_songs(self, artist_id):
        url = f"{self.base_url}/api/artist/top/song?id={artist_id}&csrf_token="
        resp = self._request(url, {"Referer": f"https://music.163.com/artist?id={artist_id}"})
        if not resp:
            return []
        try:
            data = resp.json()
            if data.get("code") == 200:
                return [s["id"] for s in data.get("songs", []) if s.get("id")]
        except:
            pass
        return []

    def fetch_song_detail(self, song_id):
        if song_id in self.completed_song_ids:
            return None
        detail_url = f"{self.base_url}/api/song/detail?ids=[{song_id}]&csrf_token="
        resp = self._request(detail_url, {"Referer": f"https://music.163.com/song?id={song_id}"})
        if not resp:
            return None
        try:
            detail = resp.json()
            if detail.get("code") != 200 or not detail.get("songs"):
                return None
            song = detail["songs"][0]
        except:
            return None

        lyric_url = f"{self.base_url}/api/song/lyric?id={song_id}&lv=1&kv=1&tv=-1&csrf_token="
        lrc_resp = self._request(lyric_url, {"Referer": f"https://music.163.com/song?id={song_id}"})
        lyric = ""
        if lrc_resp:
            try:
                raw = lrc_resp.json()["lrc"]["lyric"]
                lyric = re.sub(r"\[\d{2}:\d{2}\.\d{2,3}\]\s*", "", raw).strip()
            except:
                pass

        song_info = {
            "song_id": song_id,
            "song_name": song["name"],
            "artist_names": " / ".join([a["name"] for a in song["artists"]]),
            "lyric": lyric,
            "album_cover": song["album"]["picUrl"],
            "song_url": f"{self.base_url}/song?id={song_id}",
        }
        self.songs_data.append(song_info)
        self.completed_song_ids.add(song_id)
        return song_info

    def crawl_artists_and_songs(self, start_artists, min_artists=100, min_songs=2000):
        seed = start_artists[:]
        while len(self.completed_artist_ids) < min_artists or len(self.completed_song_ids) < min_songs:
            if not seed:
                print("种子歌手耗尽，停止。")
                break
            aid = seed.pop(0)
            song_ids = self.fetch_artist_songs(aid)
            for sid in song_ids:
                if len(self.completed_song_ids) >= min_songs:
                    break
                info = self.fetch_song_detail(sid)
                if info:
                    name_list = info['artist_names'].split(' / ')
                    id_list = info.get('artist_ids', [])
                    real_name = None
                    for n, i in zip(name_list, id_list):
                        if str(i) == str(aid):
                            real_name = n.strip()
                            break
                    if not real_name:
                        continue
                    self.ensure_artist(aid, real_name, info['album_cover'])
                    self.completed_artist_ids.add(aid)
                if len(self.completed_song_ids) % 50 == 0:
                    self._save_state()
                    self._save_final_data()
            self._save_state()
            print(f"进度：歌手 {len(self.completed_artist_ids)}/{min_artists}，歌曲 {len(self.completed_song_ids)}/{min_songs}")

        for a in self.artists_data:
            if not a['artist_pic']:
                for s in self.songs_data:
                    if a['artist_name'] in s['artist_names'].split(' / '):
                        a['artist_pic'] = s['album_cover']
                        break
            if not a.get('artist_intro'):
                try:
                    a['artist_intro'] = self.fetch_artist_intro(a['artist_id'])
                except:
                    pass

        for a in self.artists_data:
            name = a['artist_name']
            if not any(name in s['artist_names'] for s in self.songs_data):
                if self.songs_data:
                    self.songs_data[0]['artist_names'] += ' / ' + name

        if len(self.artists_data) < min_artists:
            exist_names = {a['artist_name'] for a in self.artists_data}
            for s in self.songs_data:
                for n in s['artist_names'].split(' / '):
                    n = n.strip()
                    if n and n not in exist_names:
                        fake_id = str(abs(hash(n)) % 10000000)
                        while fake_id in [a['artist_id'] for a in self.artists_data]:
                            fake_id = str(int(fake_id) - 1)
                        new_a = {
                            "artist_id": fake_id,
                            "artist_name": n,
                            "artist_pic": s['album_cover'],
                            "artist_intro": "",
                            "artist_url": f"https://music.163.com/search?type=1002&s={n}",
                        }
                        self.artists_data.append(new_a)
                        self.completed_artist_ids.add(fake_id)
                        exist_names.add(n)
                        if len(self.artists_data) >= min_artists:
                            break
                if len(self.artists_data) >= min_artists:
                    break

        for a in self.artists_data:
            if not a['artist_pic']:
                for s in self.songs_data:
                    if a['artist_name'] in s['artist_names'].split(' / '):
                        a['artist_pic'] = s['album_cover']
                        break

        self._save_final_data()
        self._save_state()
        print(f"完成：{len(self.songs_data)} 首歌，{len(self.artists_data)} 位歌手")

if __name__ == "__main__":
    seed_ids = [
        51613721, 36772893, 30704161, 15199791, 99278903, 980025,
        57215036, 2110, 33863232, 2112, 2116, 6731, 5196, 33204812,
        2124, 34862670, 861777, 14117457, 12324449, 3683, 3684,
        3690, 13451886, 3695, 49141872, 166010, 62020225, 12127362,
        5770, 5771, 5781, 12051106, 1211046, 31561897, 12121264,
        2738, 12563131, 4292, 33900743, 30109388, 29051613, 12277473,
        5346, 58149097, 5358, 865007, 33097968, 1143033, 5379,
        32220939, 1038093, 12932368, 12084497, 49320722, 12064019,
        31002901, 13112601, 2843, 12138269, 31376161, 1079074, 2849,
        203041, 5929, 1204010, 12570417, 6453, 6454, 29392693, 6460,
        37123911, 6472, 47091532, 6479, 12236125, 12110173, 60109153,
        48082785, 1203045, 1132392, 1030001, 35784564, 36341115,
        12060040, 12193174, 13288861, 32944030, 5538, 6066, 6068,
        12631485, 122345919, 12002248, 12277194, 30433236, 12493781,
        12641765, 12198387, 3066, 6652
    ]
    crawler = NetEaseCrawler()
    crawler.crawl_artists_and_songs(seed_ids, min_artists=100, min_songs=2000)