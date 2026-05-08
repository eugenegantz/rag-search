#!/usr/bin/env python3
"""
Точка входа для веб-версии.
Синоним daemon.py -- запускает единый backend с веб-интерфейсом.
"""

from daemon import start_daemon

if __name__ == "__main__":
    start_daemon()
