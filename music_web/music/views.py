import time
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Song, Artist, Comment

ITEMS_PER_PAGE = 20


def song_list(request):
    page = request.GET.get('page', 1)
    songs = Song.objects.all().order_by('id')
    paginator = Paginator(songs, ITEMS_PER_PAGE)
    try:
        songs_page = paginator.page(page)
    except PageNotAnInteger:
        songs_page = paginator.page(1)
    except EmptyPage:
        songs_page = paginator.page(paginator.num_pages)
    return render(request, 'music/song_list.html', {'songs': songs_page})


def song_detail(request, song_id):
    song = get_object_or_404(Song, pk=song_id)

    # 解析歌手名并尝试关联到已有歌手记录
    artist_names = [name.strip() for name in song.artist_names.split(' / ') if name.strip()]
    artist_links = []
    for name in artist_names:
        artist = None
        try:
            artist = Artist.objects.get(name=name)
        except Artist.DoesNotExist:
            pass
        except Artist.MultipleObjectsReturned:
            artist = Artist.objects.filter(name=name).first()

        if not artist:
            keywords = [name]
            if '（' in name:
                keywords.append(name.split('（')[0].strip())
            if '(' in name:
                keywords.append(name.split('(')[0].strip())
            query = Q()
            for kw in keywords:
                query |= Q(name__icontains=kw)
            artists = Artist.objects.filter(query)
            if artists.exists():
                artist = artists.first()

        artist_links.append({
            'name': name,
            'id': artist.id if artist else None,
        })

    # 处理评论提交
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Comment.objects.create(song=song, content=content)
        return redirect('song_detail', song_id=song_id)

    comments = song.comments.all()
    context = {
        'song': song,
        'artist_links': artist_links,
        'comments': comments,
    }
    return render(request, 'music/song_detail.html', context)


def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    song_id = comment.song_id
    comment.delete()
    return redirect('song_detail', song_id=song_id)


def artist_list(request):
    page = request.GET.get('page', 1)
    artists = Artist.objects.all().order_by('id')
    paginator = Paginator(artists, ITEMS_PER_PAGE)
    try:
        artists_page = paginator.page(page)
    except PageNotAnInteger:
        artists_page = paginator.page(1)
    except EmptyPage:
        artists_page = paginator.page(paginator.num_pages)
    return render(request, 'music/artist_list.html', {'artists': artists_page})


def artist_detail(request, artist_id):
    artist = get_object_or_404(Artist, pk=artist_id)
    raw_name = artist.name.strip()

    keywords = [raw_name]
    if '（' in raw_name and '）' in raw_name:
        parts = raw_name.split('（')
        keywords.append(parts[0].strip())
        keywords.append(parts[1].split('）')[0].strip())
    if '(' in raw_name and ')' in raw_name:
        parts = raw_name.split('(')
        keywords.append(parts[0].strip())
        keywords.append(parts[1].split(')')[0].strip())

    expanded = []
    for kw in keywords:
        parts = kw.split()
        expanded.extend(parts)
        expanded.append(kw)
    keywords = list(set(k.strip() for k in expanded if k.strip()))

    query = Q()
    for kw in keywords:
        query |= Q(artist_names__icontains=kw)
    songs = Song.objects.filter(query).distinct()

    return render(request, 'music/artist_detail.html', {'artist': artist, 'songs': songs})


def search_results(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'song')
    page = request.GET.get('page', 1)

    if not query:
        context = {
            'results': [],
            'query': query,
            'search_type': search_type,
            'count': 0,
            'elapsed': '0.000',
        }
        return render(request, 'music/search_results.html', context)

    start = time.time()
    if search_type == 'song':
        results = Song.objects.filter(
            Q(name__icontains=query) | Q(artist_names__icontains=query) | Q(lyric__icontains=query)
        ).only('id', 'name', 'artist_names', 'cover_url').order_by('id')
    else:
        results = Artist.objects.filter(
            Q(name__icontains=query) | Q(intro__icontains=query)
        ).only('id', 'name', 'pic_url').order_by('id')

    elapsed = time.time() - start
    paginator = Paginator(results, ITEMS_PER_PAGE)
    try:
        results_page = paginator.page(page)
    except:
        results_page = paginator.page(1)

    context = {
        'results': results_page,
        'query': query,
        'search_type': search_type,
        'count': paginator.count,
        'elapsed': f'{elapsed:.3f}',
    }
    return render(request, 'music/search_results.html', context)