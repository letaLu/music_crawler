import json
import pandas as pd
import matplotlib.pyplot as plt
import jieba
from wordcloud import WordCloud
from collections import Counter
import os

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

with open('netease_data/songs.json', 'r', encoding='utf-8') as f:
    songs = json.load(f)
with open('netease_data/artists.json', 'r', encoding='utf-8') as f:
    artists = json.load(f)

df_songs = pd.DataFrame(songs)
df_artists = pd.DataFrame(artists)

os.makedirs('analysis_figures', exist_ok=True)

all_lyrics = ' '.join(df_songs['lyric'].fillna('').values)

stopwords = set([
    '我', '你', '的', '了', '在', '也', '就', '都', '和', '不', '要', '有',
    '这', '那', '人', '会', '吗', '很', '他', '她', '它', '是', '吧', '啊',
    '呀', '么', '哦', '嗯', '啦', '呢', '我们', '你们', '他们', '自己',
    '没有', '什么', '怎么', '为什么', '因为', '所以', '但是', '如果',
    '一个', '一种', '一样', '这个', '那个', '可以', '已经', '还是',
    '然后', '虽然', '只是', '觉得', '知道', '不会', '不能', '不要',
    '作曲', '作词', '编曲', '制作', '出品', '监制', '混音', '母带',
    '录音', '和声', '吉他', '钢琴', '弦乐', '鼓', '贝斯', '键盘',
    'Studio', 'Music', 'by', 'feat', 'cover', 'ft.', 'the', 'me', 'you',
    'to', 'it', 'on', 'in', 'my'
])

words = jieba.lcut(all_lyrics)
filtered = [w.strip() for w in words if w not in stopwords and len(w) > 1]
word_counts = Counter(filtered)
top20 = word_counts.most_common(20)
print('高频词 Top20:', top20)

wc = WordCloud(
    font_path='simhei.ttf',
    width=800,
    height=400,
    background_color='white',
    max_words=100,
    collocations=False
).generate_from_frequencies(dict(top20))

plt.figure(figsize=(10,5))
plt.imshow(wc, interpolation='bilinear')
plt.axis('off')
plt.title('歌词高频词词云')
plt.savefig('analysis_figures/lyric_wordcloud.png', dpi=150)
plt.show()

print("分析歌手作品数...")
artist_counter = Counter()
for names in df_songs['artist_names'].fillna(''):
    for name in names.split(' / '):
        name = name.strip()
        if name:
            artist_counter[name] += 1

top_artists = artist_counter.most_common(20)
names, counts = zip(*top_artists)
plt.figure(figsize=(12,6))
plt.bar(names, counts)
plt.xticks(rotation=45, ha='right')
plt.xlabel('歌手')
plt.ylabel('歌曲数量')
plt.title('Top 20 歌手作品数量')
plt.tight_layout()
plt.savefig('analysis_figures/top_artists_songs.png', dpi=150)
plt.close()

count_dist = Counter(artist_counter.values())
plt.figure(figsize=(10,5))
plt.bar(count_dist.keys(), count_dist.values(), color='skyblue')
plt.xlabel('拥有歌曲数')
plt.ylabel('歌手人数')
plt.title('歌手拥有歌曲数量分布')
plt.xlim(0, max(count_dist.keys()))
plt.savefig('analysis_figures/artist_song_distribution.png', dpi=150)
plt.close()

print("分析歌词长度...")
df_songs['lyric_len'] = df_songs['lyric'].fillna('').apply(len)
plt.figure(figsize=(10,5))
plt.hist(df_songs['lyric_len'], bins=50, color='lightcoral', edgecolor='black')
plt.xlabel('歌词长度（字符数）')
plt.ylabel('歌曲数量')
plt.title('歌曲歌词长度分布')
plt.savefig('analysis_figures/lyric_length_hist.png', dpi=150)
plt.close()

stats = df_songs['lyric_len'].describe()
print("歌词长度统计:\n", stats)
print("全部图表已保存到 analysis_figures 文件夹。")