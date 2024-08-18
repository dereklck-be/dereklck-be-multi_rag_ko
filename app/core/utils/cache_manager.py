class CacheManager:
    def __init__(self):
        self.cache = {}

    def add_to_cache(self, key, value):
        self.cache[key] = value

    def get_from_cache(self, key):
        return self.cache.get(key)

    def clear_cache(self):
        self.cache.clear()

    def remove_from_cache(self, key):
        if key in self.cache:
            del self.cache[key]