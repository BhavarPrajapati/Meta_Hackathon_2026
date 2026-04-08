import requests
import json

try:
    import websockets
    import asyncio
    _WS_AVAILABLE = True
except ImportError:
    _WS_AVAILABLE = False


class StartupEnv:
    def __init__(self, base_url: str = "http://localhost:7860", session_id: str = "default"):
        self.base_url = base_url.rstrip("/")
        self.session_id = session_id
        self._last_state = {}

    def reset(self, task: str = "easy") -> dict:
        resp = requests.post(
            f"{self.base_url}/reset",
            json={"task": task, "session_id": self.session_id},
            timeout=10,
        )
        resp.raise_for_status()
        self._last_state = resp.json()
        return self._last_state

    def step(self, action: str) -> tuple:
        resp = requests.post(
            f"{self.base_url}/step",
            json={"action": action, "session_id": self.session_id},
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        self._last_state = result["state"]
        return (
            result["observation"],
            result["reward"],
            result["done"],
            result.get("truncated", False),
            result.get("info", {}),
        )

    def close(self):
        try:
            requests.post(
                f"{self.base_url}/close",
                json={"session_id": self.session_id},
                timeout=5,
            )
        except Exception:
            pass

    def get_state(self) -> dict:
        resp = requests.get(f"{self.base_url}/state", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def info(self) -> dict:
        resp = requests.get(f"{self.base_url}/info", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


if __name__ == "__main__":
    print("Testing OpenEnv client...")

    with StartupEnv() as env:
        env_info = env.info()
        print(f"Environment: {env_info['name']} v{env_info['version']}")
        print(f"Actions: {env_info['action_space']['actions']}")

        obs = env.reset(task="easy")
        print(f"\nReset — Valuation: ${obs['valuation']:,.0f} | MRR: ${obs['mrr']:,.0f}")

        for i in range(3):
            obs_str, reward, done, truncated, info = env.step("hire_engineer")
            print(f"Step {i+1} — Reward: {reward:.4f} | {obs_str[:60]}")
            if done:
                break

    print("\nClient test passed.")
