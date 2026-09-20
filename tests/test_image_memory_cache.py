from concurrent.futures import ThreadPoolExecutor
from PySide6.QtGui import QImage, QColor
from core.image_memory_cache import ImageMemoryCache


def image(color='red', size=10):
    result = QImage(size, size, QImage.Format.Format_ARGB32)
    result.fill(QColor(color))
    return result


def test_cache_bounds_shared_bytes_and_evicts_least_recently_used():
    cache = ImageMemoryCache(800)
    fork = cache.fork()
    cache['first'] = image()
    fork['second'] = image('blue')
    assert cache.get('first') is not None
    fork['third'] = image('green')
    assert cache.get('second') is None
    assert cache.retained_bytes == fork.retained_bytes == 800
    assert cache.get('third').pixelColor(0, 0) == QColor('green')


def test_large_image_is_not_retained_and_returned_pixels_are_isolated():
    cache = ImageMemoryCache(400)
    cache['image'] = image()
    cached = cache.get('image')
    cached.fill(QColor('blue'))
    assert cache.get('image').pixelColor(0, 0) == QColor('red')
    cache['large'] = image(size=100)
    assert cache.get('large') is None
    assert cache.retained_bytes == 400


def test_concurrent_forks_share_one_budget_without_cross_mutation():
    cache = ImageMemoryCache(4000)
    def work(index):
        fork = cache.fork()
        for count in range(50):
            key = f'{index}:{count}'
            fork[key] = image()
            stored = fork.get(key)
            if stored is not None:
                stored.fill(QColor('blue'))
        assert fork.retained_bytes <= 4000
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(work, range(8)))
    assert cache.retained_bytes <= 4000
