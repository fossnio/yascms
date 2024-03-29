import pickle

import redis

from yascms.dal import DAL


class CacheController:
    """透過 redis 實作的 cache 層"""

    def __init__(self, redis_url, prefix):
        self.redis = redis.Redis.from_url(redis_url)
        self.prefix = prefix

    def __call__(self, request):
        return self

    def get_site_config(self):
        key = f'{self.prefix}_site_config'
        cache = self.redis.get(key)
        if cache:
            return pickle.loads(cache)
        else:
            config = {config.name: config.value for config in DAL.get_site_config_list()}
            self.redis.set(key, pickle.dumps(config))
            return config

    def delete_site_config(self):
        self.redis.delete(f'{self.prefix}_site_config')
        return True

    def get_current_theme_config(self):
        key = f'{self.prefix}_current_theme_config'
        cache = self.redis.get(key)
        if cache:
            return pickle.loads(cache)
        else:
            config = DAL.get_theme_config(self.get_current_theme_name())
            self.redis.set(key, pickle.dumps(config))
            return config

    def delete_current_theme_config(self):
        self.redis.delete(f'{self.prefix}_current_theme_config')
        return True

    def get_current_theme_name(self):
        key = f'{self.prefix}_current_theme_name'
        cache = self.redis.get(key)
        if cache:
            return cache.decode('utf8')
        else:
            current_theme = DAL.get_current_theme_name()
            self.redis.set(key, current_theme)
            return current_theme

    def delete_current_theme_name(self):
        self.redis.delete(f'{self.prefix}_current_theme_name')
        return True

    def get_available_theme_name_list(self):
        key = f'{self.prefix}_available_theme_name_list'
        cache = self.redis.get(key)
        if cache:
            return pickle.loads(cache)
        else:
            available_theme_name_list = DAL.get_available_theme_name_list()
            self.redis.set(key, pickle.dumps(available_theme_name_list))
            return available_theme_name_list

    def delete_available_theme_name_list(self):
        self.redis.delete(f'{self.prefix}_available_theme_name_list')
        return True
