# tests/test_images.py
from pipeline.images import resolve_image_urls, is_placeholder_size

def test_direct_reddit_image():
    assert resolve_image_urls("https://i.redd.it/abc123.jpeg", {}) == \
        ["https://i.redd.it/abc123.jpeg"]

def test_imgur_single():
    assert resolve_image_urls("https://imgur.com/VE91MNZ", {}) == \
        ["https://i.imgur.com/VE91MNZ.jpeg"]

def test_imgur_single_with_ext():
    assert resolve_image_urls("https://imgur.com/VE91MNZ.png", {}) == \
        ["https://i.imgur.com/VE91MNZ.png"]

def test_reddit_gallery_uses_media_metadata():
    post = {
        "is_gallery": True,
        "media_metadata": {
            "aaa": {"s": {"u": "https://preview.redd.it/aaa.jpg?width=1200&amp;s=x"}},
            "bbb": {"s": {"u": "https://preview.redd.it/bbb.jpg?width=1200&amp;s=y"}},
        },
        "gallery_data": {"items": [{"media_id": "aaa"}, {"media_id": "bbb"}]},
    }
    assert resolve_image_urls("https://www.reddit.com/gallery/xyz", post) == [
        "https://preview.redd.it/aaa.jpg?width=1200&s=x",
        "https://preview.redd.it/bbb.jpg?width=1200&s=y",
    ]

def test_placeholder_size_detection():
    assert is_placeholder_size((161, 81)) is True
    assert is_placeholder_size((1200, 900)) is False
    assert is_placeholder_size((30, 20)) is True   # suspiciously tiny
