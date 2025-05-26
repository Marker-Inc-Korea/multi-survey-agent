# 📞 AI 에이전트로 다단계 전화 설문조사 자동화하기

LiveKit Agents SDK, OpenAI Realtime API, Twilio Elastic SIP Trunking을 결합하여 사람이 전화를 걸고 응답을 기록하던 작업을 모두 코드로 처리할 수 있습니다.

## 주요 기능

* **선언형 설문 흐름**: `survey_questions.yaml` 파일만 수정하여 질문, 선택지, 조건 분기 관리
* **자동 발신**: `survey_data.csv`를 읽어 Twilio SIP 트렁크로 대상자에게 자동으로 전화
* **AI 대화 엔진**: OpenAI Realtime API로 STT·LLM·TTS를 단일 모델로 저지연 처리
* **상태 관리**: `SurveyState`를 통해 답변 완료, 건너뜀, 다음 질문 추적
* **결과 기록**: CSV에 응답 저장 및 `Status=Completed` 표시로 재발신 방지

## 디렉터리 구조

```
├── make_survey_call.py            # 설문 대상자 읽어 에이전트 디스패치 및 전화 발신
├── multi_survey_calling_agent.py  # LiveKit Agent 기반 다단계 설문 로직
├── schema.py                      # QuestionRecord, SurveyState 데이터 클래스
├── utils.py                       # 설문 흐름과 프롬프트 로드 헬퍼
├── survey_questions.yaml          # 설문 흐름 정의 (ID, 텍스트, 옵션, 조건)
├── survey_data.csv                # 대상자 목록 및 응답 저장
└── .env.example                   # 환경 변수 예시 파일
```

## 사전 준비

* **Python 3.12 이상**
* **LiveKit 서버** (Agents SDK 활성화)
* **OpenAI API 키** (Realtime API 권한 포함)
* **Twilio Elastic SIP Trunking** 계정 및 SIP Trunk SID

## 설치 및 환경 설정

1. 저장소 복제

   ```bash
   git clone https://github.com/Marker-Inc-Korea/multi-survey-agent.git
   cd multi-survey-agent
   ```
2. 의존성 설치

    uv를 이용해 필요한 파이썬 패키지를 한 번에 설치합니다.

   ```bash
   uv sync
   ```
3. 환경 변수 구성

   * `.env.example`를 `.env`로 복사 후 다음 값을 채워 넣습니다:

     ```dotenv
     OPENAI_API_KEY=sk-...
     LIVEKIT_API_KEY=...
     LIVEKIT_API_SECRET=...
     LIVEKIT_URL=wss://your.livekit.server
     SIP_OUTBOUND_TRUNK_ID=your_twilio_trunk_sid
     ```

## 설문 흐름 정의 (`survey_questions.yaml`)

YAML 파일에서 설문 질문과 분기 조건을 선언합니다. 

## 대상자 목록 준비 (`survey_data.csv`)

CSV에 대상자 전화번호와 행 번호를 입력하고, `Answer`와 `Status` 칸은 비워 둡니다.

```csv
PhoneNumber,RowIndex,Answer,Status
+821012345678,1,,
+821098765432,2,,
```

설문이 완료되면 스크립트가 `Answer`에 JSON 형태로 응답을 기록하고, `Status`를 `Completed`로 업데이트합니다.

## 🚀 사용 방법

### 1. 에이전트 실행

터미널에서 다음 명령으로 에이전트를 개발 모드로 실행합니다:

```bash
python multi_survey_calling_agent.py dev
```

LiveKit 서버에 접속하여 설문 요청을 대기합니다.

### 2. 설문 발신 스크립트 실행

다른 터미널에서 CSV를 읽어 설문 전화를 겁니다:

```bash
python make_survey_call.py
```

* 완료된 대상은 자동 건너뛰기
* 각 대상에 대해 Agent Dispatch → SIP Call 순서로 실행

### 3. 결과 확인

* 콘솔 로그에서 통화 연결 상태, VAD 감지 시점, 에러 여부 확인
* `survey_data.csv`에 응답 내용과 `Completed` 상태가 자동 기록

## 🏷️ License

MIT © Marker-Inc-Korea