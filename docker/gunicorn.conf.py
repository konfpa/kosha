import os

bind = "0.0.0.0:8000"

# Threads for concurrency: requests mostly wait on the database, and a waiting
# thread costs a stack where a waiting process costs an interpreter.
worker_class = "gthread"

# Not derived from os.cpu_count(): inside a container it reports the host's
# cores, not the container's CPU limit.
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))

# Recycling bounds memory growth; jitter stops every worker restarting at once.
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "100"))

preload_app = True
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "30"))

# Must stay below stop_grace_period in compose.prod.yaml, or Docker kills
# workers mid-drain.
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))

# The control socket defaults to a directory under /app, which is read-only.
control_socket_disable = True

# The default tmp dir may be disk-backed, where a slow heartbeat write gets a
# healthy worker killed as hung.
worker_tmp_dir = "/dev/shm"

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%({x-forwarded-for}i)s %(t)s "%(r)s" %(s)s %(b)s %(M)sms "%(a)s"'

# The proxy reaches the container via Docker's bridge gateway, not 127.0.0.1.
# Trusting any peer is safe only because compose.prod.yaml publishes the port
# on loopback; change that binding and this must change with it.
forwarded_allow_ips = os.environ.get("GUNICORN_FORWARDED_ALLOW_IPS", "*")
