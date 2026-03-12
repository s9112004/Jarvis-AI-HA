import threading
import time


class NetworkHealth:
    def __init__(self):
        self._lock = threading.Lock()
        self._services = {}
        self._default_threshold = 3
        self._base_cooldown = 15
        self._max_cooldown = 300

    def _ensure(self, service_name: str):
        if service_name not in self._services:
            self._services[service_name] = {
                "status": "ONLINE",              # ONLINE / DEGRADED / OFFLINE
                "consecutive_failures": 0,
                "last_error": None,
                "last_success_at": None,
                "last_failure_at": None,
                "opened_until": 0,
                "cooldown_seconds": 0,
            }
        return self._services[service_name]

    def mark_success(self, service_name: str):
        with self._lock:
            state = self._ensure(service_name)
            state["status"] = "ONLINE"
            state["consecutive_failures"] = 0
            state["last_error"] = None
            state["last_success_at"] = time.time()
            state["opened_until"] = 0
            state["cooldown_seconds"] = 0

    def mark_failure(self, service_name: str, error: Exception | str):
        with self._lock:
            state = self._ensure(service_name)
            state["consecutive_failures"] += 1
            state["last_error"] = str(error)
            state["last_failure_at"] = time.time()

            failures = state["consecutive_failures"]
            if failures >= self._default_threshold:
                cooldown = min(
                    self._base_cooldown * (2 ** (failures - self._default_threshold)),
                    self._max_cooldown
                )
                state["status"] = "OFFLINE"
                state["cooldown_seconds"] = cooldown
                state["opened_until"] = time.time() + cooldown
            else:
                state["status"] = "DEGRADED"
                state["cooldown_seconds"] = 0
                state["opened_until"] = 0

    def can_attempt(self, service_name: str):
        with self._lock:
            state = self._ensure(service_name)
            if state["status"] != "OFFLINE":
                return True, 0

            now = time.time()
            if now >= state["opened_until"]:
                return True, 0

            wait_seconds = max(1, int(state["opened_until"] - now))
            return False, wait_seconds

    def get_status(self, service_name: str):
        with self._lock:
            state = self._ensure(service_name).copy()
            now = time.time()

            if state["status"] == "OFFLINE" and now >= state["opened_until"]:
                # 冷卻時間到了，允許重新測試，但狀態先維持 DEGRADED
                state["status"] = "DEGRADED"

            if state["opened_until"] > now:
                state["retry_after_seconds"] = max(1, int(state["opened_until"] - now))
            else:
                state["retry_after_seconds"] = 0

            return state

    def snapshot(self):
        with self._lock:
            names = list(self._services.keys())

        return {name: self.get_status(name) for name in names}


network_health = NetworkHealth()