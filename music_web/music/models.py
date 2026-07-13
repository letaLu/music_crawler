from django.db import models

class Artist(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    pic_url = models.URLField(max_length=500, blank=True)
    intro = models.TextField(blank=True)
    origin_url = models.URLField(max_length=500)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['id']),
        ]
        ordering = ['id']

    def __str__(self):
        return self.name

class Song(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    artist_names = models.CharField(max_length=500, db_index=True)
    lyric = models.TextField(blank=True)
    cover_url = models.URLField(max_length=500)
    origin_url = models.URLField(max_length=500)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['artist_names']),
            models.Index(fields=['id']),
        ]
        ordering = ['id']

    def __str__(self):
        return self.name

class Comment(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # 新评论在前
        indexes = [
            models.Index(fields=['song', '-created_at']),
        ]

    def __str__(self):
        return self.content[:30]