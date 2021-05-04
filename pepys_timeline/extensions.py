from flask_cors import CORS
from flask_cachebuster import CacheBuster

cors = CORS()

cache_buster = CacheBuster(config={
    'extensions': ['.js', '.css', '.csv'],
    'hash_size': 5
})
