
---
### Multi RAG CHATBOT
Fast API + Open AI

---

### 애플리케이션 설명서 

프로젝트 실행을 위한 세팅 방법과 진행 순서가 담긴 설명서입니다. (python 3.9.6)

- 애플리케이션은 MVC 패턴으로 설계되어 있습니다. 로컬에서 실행할 때는 별도의 데이터베이스 설정 없이 OpenAI API 키만 .env.local 파일에 입력하면 됩니다. 벡터 서치를 위해 sentence_transformer로 'upskyy/kf-deberta-multitask' 모델이 사용되었습니다.

- PDF를 업로드하고 ingest를 시작하면, 테이블 데이터와 텍스트 데이터가 페이지별로 처리된 후 InMemory에 쌓여 Chunk 방식으로 전처리가 진행됩니다. 이 과정에서 bm25를 위한 JSONL 형태의 전처리와 context 기반의 데이터 전처리가 이루어지며, 각 모델이 참조할 컬렉션에 저장됩니다. 경량화된 컴퓨팅 환경에서는 전처리 시, 메모리 부하가 발생할 수 있습니다. 


```shell

### 프로젝트 구조

프로젝트 구조는 다음과 같습니다:

```shell
dereklck-be-multi_rag_ko/
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── ingest_data.py
│   │   │   │   ├── answer_question.py
│   │   │   │   └── search_vector.py
│   │   │   └── __init__.py
│   │   └── v2/
│   │       └── __init__.py
│   ├── core/
│   │   ├── embeddings/
│   │   │   ├── __init__.py
│   │   │   └── initializers.py
│   │   ├── preprocessors/
│   │   │   ├── header_processor.py
│   │   │   ├── table_processor.py
│   │   │   └── text_splitter.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── cache_manager.py
│   │   │   ├── common.py
│   │   │   ├── platform.py
│   │   │   ├── progress_utils.py
│   │   │   ├── error_handler.py
│   │   │   └── success_handler.py
│   │   ├── database/
│   │   │   ├── chroma/
│   │   │   └── (Chroma 관련 파일들)
│   │   ├── pdfs/
│   │   │   └── (PDF 저장소 관련 파일들)
│   │   └── textdb/
│   │       └── (텍스트 DB 관련 파일들)
│   ├── models/
│   │   ├── state.py
│   │   ├── __init__.py
│   │   ├── chroma_repository.py
│   │   └── text_repository.py
│   ├── services/
│   │   ├── answer_service.py
│   │   ├── ingest_service.py
│   │   └── search_service.py
│   ├── .env.local
│   ├── .env.dev
│   ├── .env.prod
│   ├── .env.stg
│   ├── main.py
│   └── config.py
├── streamlit_app/
│   ├── components/
│   │   ├── display_output.py
│   │   ├── text_input.py
│   │   ├── file_input.py
│   │   ├── submit_button.py
│   │   └── image_input.py
│   ├── utils/
│   │   ├── request_handler.py
│   │   ├── api_manager.py
│   │   └── validation_checker.py
│   ├── .env.local
│   ├── .env.stg
│   ├── .env.dev
│   ├── .env.prod
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── templates
│   └── layout.py
├── tests/
│   ├── test_api.py
│   ├── test_database.py
│   ├── test_llm.py
│   ├── test_proprocessor.py
│   └── test_retriever.py
└── README.md
```

---

### 애플리케이션 실행

#### Python 버전 설정

이 프로젝트는 Python 3.9.6 버전을 사용합니다. Python 설치 후, 가상환경을 만들어 사용하시면 됩니다.

---

#### 가상환경 설정 및 패키지 설치

가상환경을 생성하고, 프로젝트에 필요한 패키지를 설치합니다.

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 필요 패키지 설치
pip install -r requirements.txt
```

---

#### 환경변수 설정

설정 파일을 로드하기 위해 `.env.local`, `.env.dev`, `.env.prod`, `.env.stg` 파일을 생성합니다. 이 파일에는 필요한 환경 변수를 설정합니다. 로컬에서 사용하실 경우 `app` 폴더 하위에 있는 `.env.local`의 `OPENAI_API_KEY`만 수정하시면 됩니다.

```ini
# app/.env.local
DEBUG=True
HOST=127.0.0.1
PORT=8000
DATABASE_URL=sqlite:///./local.db
OPENAI_API_KEY=your_openai_key
TOKENIZERS_PARALLELISM=false
UPLOAD_DIRECTORY=app/database/pdfs/
CHROMA_DIRECTORY=app/database/chroma/
TEXT_REPOSITORY_PATH=app/database/textdb/

# streamlit_app/.env.local
PORT=8000
HOST=127.0.0.1
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
STREAMLIT_PORT=8501
```

---

#### 애플리케이션 실행

`server.py` 스크립트를 실행하여 백엔드와 프론트엔드를 동시에 구동합니다.

```bash
python server.py
```

이 명령은 두 개의 프로세스를 각각 다른 포트에서 실행하여 백엔드(Uvicorn)와 프론트엔드(Streamlit)를 동시에 구동합니다.

---

### 애플리케이션 실행 순서 


1. **PDF 파일 업로드:** Streamlit 인터페이스에서 PDF 파일을 업로드하고, 원하는 `collection_name` 을 입력합니다.
> **Tip:** 컬렉션 이름은 언더스코어와 영어 소문자 조합을 사용하는 것을 추천드립니다.(예: `collection_test`, `finance_data`).

2. **Ingest 버튼 클릭:** `Ingest` 버튼을 누르면 파일이 서버로 전송되고, 백엔드 로그에 `tqpm`을 통한 프로세싱 단계가 나타나며 인제스트 프로세스가 시작됩니다.

3. **프로세스 완료 기다림:** 인제스트 과정이 완료될 때까지 기다립니다. 백엔드 로그를 통해 진행 상황을 확인할 수 있습니다.

4. **챗봇 이용:** 처리 완료 후에는 챗봇을 통해 질문을 입력하고 답변을 받을 수 있습니다. 챗에 사용할 컬렉션은 사용자가 입력한 `collection_name`으로 `자동`으로 참조됩니다.


---

### Streamlit 인터페이스 사용

Streamlit 인터페이스에 접속하여 데이터를 인제스트하고, 질문을 할 수 있습니다. 백엔드 구동이 끝난 후, streamlit_app이 자동으로 실행 될 것입니다. 만약 실행되지 않는다면 웹 브라우저에서 `http://localhost:8501` 또는, 이미 해당 포트가 사용중일 경우 대신 배정된 포트를 활용하여 웹 브라우저를 여시면 됩니다. 

---

### 인메모리 방식 및 캐시 관리

이 애플리케이션은 인메모리 방식으로 데이터를 처리하므로 캐시가 저장소로 사용됩니다. Ram을 조금 더 사용하게 되며, 작업 후 캐시는 자동으로 삭제됩니다. 이를 통해 메모리 사용량을 관리합니다.

---

### 데이터 저장

database 폴더에는 `sentence-transformer`로 벡터화된 `chroma_collection`과 `BM25`로 처리된 `jsonl` 파일이 저장됩니다.

---

### 상세 설명

- `environment variables`: `.env.local` 파일에서 환경변수를 설정하고 이를 로드합니다.
- `포트 관리`: `PortManager` 클래스를 사용하여 사용 가능한 포트를 찾고, 필요한 경우 기존 프로세스를 종료합니다.
- `백엔드 실행`: `ApplicationRunner` 클래스의 `run_backend` 메서드를 호출하여 Uvicorn을 사용해 백엔드를 실행합니다.
- `프론트엔드 실행`: `ApplicationRunner
- `프론트엔드 실행`: `ApplicationRunner

---

### Comment 
- 최대한 로컬 환경 및 리소스 활용하여 RAG 테스트가 가능하도록 작업 되었습니다.
- 이제 애플리케이션을 실행하여 PDF 파일을 업로드하고, 질문에 대한 답변을 얻으시면 됩니다.




