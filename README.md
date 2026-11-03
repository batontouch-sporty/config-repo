# Sporty_v2 Config Repo

Config Server(`config-service`, 8888)가 읽는 설정 저장소입니다. 서비스는 기동할 때 이 저장소의 설정을 받고, Config Server에 붙지 못하면 기동하지 않습니다.

## 파일 구조

| 파일 | 내용 |
| --- | --- |
| `application.yml` | 전 서비스 공통: Eureka 인스턴스, Actuator 노출·지표 태그, 추적 샘플링, JPA dialect, Kafka 공통값, RabbitMQ 계정, 로그 레벨 |
| `<서비스명>.yml` | 프로필과 무관한 서비스 고유 설정: Gateway 라우트, DB 계정, Feign·CB, AI·시설·탈퇴 설정 등 |
| `<서비스명>-<프로필>.yml` | 그 서비스의 환경별 값: DB URL, Kafka·Redis·RabbitMQ·Zipkin·Eureka 주소, CORS·Prometheus 주소 |

- `<서비스명>`은 `spring.application.name`과 같습니다: `gateway-service`, `user-service`, `match-service`, `facility-service`, `ai-service`, `notification-service`
- 프로필은 `local`(IDE), `dev`(Compose), `prod`(K8s) 세 개이고, 서비스마다 세 프로필 파일이 모두 있습니다(6 × 3 = 18개)
- 우선순위: `<서비스명>-<프로필>.yml` > `<서비스명>.yml` > `application.yml`. 환경변수는 이 파일들보다 우선합니다
- discovery-service, config-service는 이 저장소를 읽지 않습니다

## 프로필별 접속 주소

| 대상 | local | dev | prod |
| --- | --- | --- | --- |
| Eureka | `localhost:8761` | `discovery-service:8761` | `discovery-service:8761` |
| Zipkin | `localhost:${ZIPKIN_HOST_PORT:9411}` | `zipkin:9411` | `zipkin:9411` |
| MariaDB | `localhost:${MARIADB_HOST_PORT:3306}` | `mariadb:3306` | `${MARIADB_HOST}:${MARIADB_HOST_PORT:3306}` |
| Redis (user) | `localhost:${REDIS_HOST_PORT:6379}` | `redis:6379` | `${REDIS_HOST}:${REDIS_HOST_PORT:6379}` |
| Kafka | `localhost:${KAFKA_HOST_PORT:9092}` | `kafka:29092` | `${KAFKA_BOOTSTRAP_SERVERS}` |
| RabbitMQ (Bus, 6개 서비스) | `localhost:${RABBITMQ_HOST_PORT:5672}` | `rabbitmq:5672` | `${RABBITMQ_HOST}:${RABBITMQ_PORT:5672}` |
| Prometheus (gateway) | `localhost:9090` | `prometheus:9090` | `${PROMETHEUS_URL}` |
| CORS 허용 출처 (gateway) | `localhost:3000` | `localhost:3000` | `${CORS_ALLOWED_ORIGIN}` |

local은 Compose가 127.0.0.1에 연 포트로 붙습니다. 포트는 backend의 `.env`(`*_HOST_PORT`)를 따릅니다.
prod의 Eureka·Zipkin은 같은 Namespace의 K8s Service 이름을 기본값으로 씁니다. DB·Kafka·Redis·RabbitMQ·모니터링은 K8s 밖 infra EC2에 있어 기본값이 없습니다.

## prod에서 넣어야 하는 환경변수

| 환경변수 | 쓰는 서비스 | 비고 |
| --- | --- | --- |
| `MARIADB_HOST` | user·match·facility·notification | infra EC2 주소. `MARIADB_HOST_PORT`는 기본 3306 |
| `KAFKA_BOOTSTRAP_SERVERS` | user·match·notification | 예: `<infra 주소>:9092` |
| `REDIS_HOST` | user | `REDIS_HOST_PORT`는 기본 6379 |
| `RABBITMQ_HOST` | 6개 서비스 | infra EC2 주소. `RABBITMQ_PORT`는 기본 5672 |
| `PROMETHEUS_URL` | gateway | 예: `http://<infra 주소>:9090` |
| `CORS_ALLOWED_ORIGIN` | gateway | 프론트 주소 |
| `JWT_SECRET_KEY` | gateway·user | 비밀값 |
| `RABBITMQ_USER`, `RABBITMQ_PASSWORD` | 6개 서비스 | 비밀값. local·dev도 backend `.env`의 같은 이름 값을 쓴다 |
| `USER_APP_PASSWORD`, `MATCH_APP_PASSWORD`, `FACILITY_APP_PASSWORD`, `NOTIFICATION_APP_PASSWORD` | 각 서비스 | 비밀값 |
| `OPENAI_API_KEY`, `PUBLIC_DATA_API_KEY` | ai, facility | 비밀값. 없으면 기능만 꺼진다 |

`EUREKA_URL`, `MANAGEMENT_ZIPKIN_TRACING_ENDPOINT`는 K8s Service 이름이 다를 때만 넣습니다.

## 비밀값

DB 비밀번호, 토큰 시크릿, API 키는 평문으로 올리지 않습니다. `${환경변수}`로 두거나 `{cipher}`로 암호화해서 넣습니다. CI가 평문을 막습니다.

### `{cipher}` 규칙

- `{cipher}` 암호문은 prod 파일(`<서비스명>-prod.yml`)에만 넣습니다. local·dev는 `${환경변수}`를 그대로 씁니다.
- 값은 작은따옴표로 감쌉니다: `password: '{cipher}AQB2...'`. 따옴표가 없으면 YAML이 `{`를 객체로 읽습니다.
- 암호문은 키스토어를 가진 사람이 config-service의 `/encrypt`로 만듭니다. 키스토어 만들기, 환경변수, 암호문 만드는 법은 [backend config-service 안내](https://github.com/batontouch-sporty/backend/blob/main/config-service/README.md)를 봅니다.
- Config Server가 복호화해서 서비스에 평문을 내려 줍니다. 키가 없거나 틀린 Config Server는 그 값을 `invalid.<키>`로 바꿔 내려 주므로 서비스가 값 없이 뜨다 실패합니다.
- 키를 바꾸면 기존 암호문을 모두 다시 만들어 넣습니다.

## 설정 새로고침 (Spring Cloud Bus)

이 저장소를 바꾸고 main에 머지한 뒤 config-service의 `POST /actuator/busrefresh`를 한 번 부르면 RabbitMQ를 거쳐 6개 서비스가 재시작 없이 설정을 다시 읽습니다. 로그 레벨(`logging.level.*`)과 `@ConfigurationProperties` 값이 바로 바뀌고, 기동 때만 읽는 값(DB 연결, 포트 등)은 재시작해야 바뀝니다. 절차는 [backend README](https://github.com/batontouch-sporty/backend#설정-새로고침-spring-cloud-bus)를 봅니다.
