"""check_secrets.py가 평문은 잡고 허용 형식은 통과시키는지 확인한다."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from check_secrets import find_in_properties, find_in_yaml

BLOCKED_YAML = [
    "password: hunter2",
    '"password": hunter2',
    "items:\n  - password: hunter2",
    "apiKey: hunter2",
    "api_key: hunter2",
    "password: hunter2 # ${DB_PASSWORD}",
    'password: "{hunter2}"',
    "password: ${DB_PASSWORD:hunter2}",
    "password: 12345",
    "jwt:\n  secret: hunter2",
]
ALLOWED_YAML = [
    'password: "{cipher}abc123"',
    "password: ${DB_PASSWORD}",
    "password: ${DB_PASSWORD_1}",
    "password: ${DB_PASSWORD:}",
    "password:",
    "token-expire-seconds: 3600",
    "username: sporty",
]

for text in BLOCKED_YAML:
    assert list(find_in_yaml(text)), f"잡아야 함: {text}"
for text in ALLOWED_YAML:
    assert not list(find_in_yaml(text)), f"통과해야 함: {text}"

assert list(find_in_properties("spring.datasource.password=hunter2"))
assert list(find_in_properties("api.key: hunter2"))
assert not list(find_in_properties("spring.datasource.password={cipher}abc"))
assert not list(find_in_properties("# password=hunter2"))
print("ok")
