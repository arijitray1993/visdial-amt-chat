var config = {}

config.db = {
    "user": "v20q",
    "name": "v20q",
    "pass": "ENTER_PASSWORD_HERE"
}

config.redis = {
    "port": 6380,
    "pass": "REDIS_PASSWORD_HERE",
    "list": "v20q_queue"
}

config.root = '/path/to/v20q/nodejs/'

module.exports = config
