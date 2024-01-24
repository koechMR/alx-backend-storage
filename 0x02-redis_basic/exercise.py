#!/usr/bin/env python3
'''Redis NoSQL '''
import uuid
import redis
from functools import wraps
from typing import Any, Callable, Union


def count_calls(method: Callable) -> Callable:
    '''Tracks '''
    @wraps(method)
    def invoker(self, *args, **kwargs) -> Any:
        ''' incrementing its call count for the key
        '''
        if isinstance(self._redis, redis.Redis):
            self._redis.incr(method.__qualname__)
        return method(self, *args, **kwargs)
    return invoker


def call_history(method: Callable) -> Callable:
    '''method in a Cache class '''
    @wraps(method)
    def invoker(self, *args, **kwargs) -> Any:
        '''storing its inputs
        '''
        in_key = '{}:inputs'.format(method.__qualname__)
        out_key = '{}:outputs'.format(method.__qualname__)
        if isinstance(self._redis, redis.Redis):
            self._redis.rpush(in_key, str(args))
        output = method(self, *args, **kwargs)
        if isinstance(self._redis, redis.Redis):
            self._redis.rpush(out_key, output)
        return output
    return invoker


def replay(f: Callable) -> None:
    '''Displays the call history
    '''
    if f is None or not hasattr(f, '__self__'):
        return
    redis_store = getattr(f.__self__, '_redis', None)
    if not isinstance(redis_store, redis.Redis):
        return
    fxn_name = f.__qualname__
    in_key = '{}:inputs'.format(fxn_name)
    out_key = '{}:outputs'.format(fxn_name)
    fxn_call_count = 0
    if redis_store.exists(fxn_name) != 0:
        fxn_call_count = int(redis_store.get(fxn_name))
    print('{} was called {} times:'.format(fxn_name, fxn_call_count))
    fx_inputs = redis_store.lrange(in_key, 0, -1)
    fx_outputs = redis_store.lrange(out_key, 0, -1)
    for fx_input, fx_output in zip(fx_inputs, fx_outputs):
        print('{}(*{}) -> {}'.format(
            fxn_name,
            fx_input.decode("utf-8"),
            fx_output,
        ))


class Cache:
    '''object for storing data
    '''
    def __init__(self) -> None:
        '''Init a Cache
        '''
        self._redis = redis.Redis()
        self._redis.flushdb(True)

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        '''Stores Redis data storage
        '''
        data_key = str(uuid.uuid4())
        self._redis.set(data_key, data)
        return data_key

    def get(
            self,
            key: str,
            fn: Callable = None,
            ) -> Union[str, bytes, int, float]:
        '''Get Redis data
        '''
        data = self._redis.get(key)
        return fn(data) if fn is not None else data

    def get_str(self, key: str) -> str:
        '''Redis data storage
        '''
        return self.get(key, lambda c: c.decode('utf-8'))

    def get_int(self, key: str) -> int:
        '''Ret an integer value
        '''
        return self.get(key, lambda c: int(c))
