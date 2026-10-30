"""설정 파일의 평문 비밀값을 찾는다. 값은 {cipher} 또는 환경변수 참조만 허용한다."""
import pathlib
import re
import sys

import yaml

SECRET_WORDS = ("password", "passwd", "pwd", "secret", "apikey", "privatekey", "token", "credential")
ENV_REFERENCE = re.compile(r"\$\{[A-Za-z0-9_.-]+:?\}")


def is_secret_key(key):
    normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
    return any(word in normalized for word in SECRET_WORDS)


def is_allowed(key, value):
    if value is None or isinstance(value, bool) or value == "":
        return True
    # 토큰 만료 시간 같은 숫자 설정은 비밀값이 아니다. 비밀번호는 숫자여도 막는다.
    if isinstance(value, (int, float)) and "password" not in str(key).lower():
        return True
    text = str(value).strip()
    return text.startswith("{cipher}") or ENV_REFERENCE.fullmatch(text) is not None


def walk(node, key=""):
    if isinstance(node, dict):
        for child_key, child in node.items():
            yield from walk(child, child_key)
    elif isinstance(node, list):
        for child in node:
            yield from walk(child, key)
    elif is_secret_key(key) and not is_allowed(key, node):
        yield key


def find_in_yaml(text):
    for document in yaml.safe_load_all(text):
        yield from walk(document)


def find_in_properties(text):
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "!")):
            continue
        key, _, value = re.match(r"([^=:\s]+)\s*([=:]?)\s*(.*)", line).groups()
        yield from walk({key: value})


def scan(root):
    found = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or {".git", ".github"} & set(path.relative_to(root).parts):
            continue
        finder = {".yml": find_in_yaml, ".yaml": find_in_yaml, ".properties": find_in_properties}.get(path.suffix)
        if finder:
            found += [f"{path.relative_to(root)}: {key}" for key in finder(path.read_text(encoding="utf-8"))]
    return found


if __name__ == "__main__":
    problems = scan(pathlib.Path("."))
    for problem in problems:
        print(f"::error::평문 비밀값: {problem}")
    if problems:
        print("{cipher}로 암호화하거나 환경변수(${NAME})로 바꿔 주세요.")
    sys.exit(1 if problems else 0)
