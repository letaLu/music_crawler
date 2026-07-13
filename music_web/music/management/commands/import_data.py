import json
import os
from django.core.management.base import BaseCommand
from music.models import Artist, Song

class Command(BaseCommand):
    help = '从 netease_data 目录导入 songs.json 和 artists.json'

    def handle(self, *args, **options):
        base_dir = r"D:\[26summer] python\hw_crawler\netease_data"

        artists_file = os.path.join(base_dir, 'artists.json')
        if os.path.exists(artists_file):
            with open(artists_file, 'r', encoding='utf-8') as f:
                artists = json.load(f)
            count = 0
            for a in artists:
                if a.get('artist_name') in ('网易云音乐', '未知', '', None):
                    continue
                Artist.objects.update_or_create(
                    id=a['artist_id'],
                    defaults={
                        'name': a['artist_name'],
                        'pic_url': a.get('artist_pic', ''),
                        'intro': a.get('artist_intro', ''),
                        'origin_url': a.get('artist_url', '')
                    }
                )
                count += 1
            self.stdout.write(self.style.SUCCESS(f'成功导入 {count} 位歌手'))
        else:
            self.stdout.write(self.style.ERROR(f'未找到文件: {artists_file}'))

        songs_file = os.path.join(base_dir, 'songs.json')
        if os.path.exists(songs_file):
            with open(songs_file, 'r', encoding='utf-8') as f:
                songs = json.load(f)
            count = 0
            for s in songs:
                Song.objects.update_or_create(
                    id=s['song_id'],
                    defaults={
                        'name': s['song_name'],
                        'artist_names': s['artist_names'],
                        'lyric': s.get('lyric', ''),
                        'cover_url': s.get('album_cover', ''),
                        'origin_url': s.get('song_url', '')
                    }
                )
                count += 1
            self.stdout.write(self.style.SUCCESS(f'成功导入 {count} 首歌曲'))
        else:
            self.stdout.write(self.style.ERROR(f'未找到文件: {songs_file}'))