# Sporty_v2 Config Repo

Config Server(`config-service`, 8888)가 읽는 설정 저장소입니다.

- 파일 이름: `application.yml`(전 서비스 공통), `<서비스명>.yml`, `<서비스명>-<프로필>.yml`
- 프로필: `local`(IDE), `dev`(Compose), `prod`(K8s)
- DB 비밀번호, 토큰 시크릿, API 키는 평문으로 올리지 않고 `{cipher}`로 암호화해서 넣습니다.
