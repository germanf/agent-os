"""Shared configuration constants for the dashboard backend."""

# File Upload Limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_TOTAL_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_FILES = 10

# Job Retention
JOB_RETENTION_SECONDS = 60 * 60  # 1 hour
MAX_FINISHED_JOBS = 200

# Paths
VAULT_DIR = "/home/ubuntu/vault"  # only exists on the production VM

# Rate Limits (requests per minute)
RATE_LIMIT_DEFAULT = "30/minute"
RATE_LIMIT_CHAT_SEND = "10/minute"
RATE_LIMIT_UPLOAD = "3/minute"
RATE_LIMIT_HEALTH = "60/minute"
