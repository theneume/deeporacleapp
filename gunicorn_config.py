import os

bind = "0.0.0.0:{}".format(os.environ.get('PORT', 9009))
workers = 1
worker_class = "sync"
timeout = 120
keepalive = 5