import logging
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from typing import Optional, List, Dict, Any
from app.models.state import initial_app_state
from app.services.search_service import SearchService
from langchain_core.messages import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)

BLACKLIST_RESPONSE = "유효한 답변을 찾지 못했습니다. 다른 질문을 해주세요."


class AnswerService:
    def __init__(self, model_name: Optional[str] = "gpt-3.5-turbo"):
        self.model_name = model_name
        self.llm = ChatOpenAI(model_name=self.model_name)

    async def get_answer(self, query: str, chat_history: List[Dict[str, Any]], collection_name: str):
        logger.info(f"Query: {query}")
        logger.info(f"Chat History: {chat_history}")
        logger.info(f"Using collection: {collection_name}")

        search_service = SearchService(collection_name=collection_name, query=query, app_state=initial_app_state)
        relevant_docs = await search_service.get_relevant_documents()

        if relevant_docs["status"] == "error":
            return BLACKLIST_RESPONSE

        context = "\n".join([doc["page_content"] for doc in relevant_docs["results"]])
        logger.info(f"Retrieved context: {context}")

        prepared_chat_history = [
            HumanMessage(content=entry["content"]) if entry["role"] == "user" else AIMessage(content=entry["content"])
            for entry in chat_history
        ]
        logger.info(f"Prepared Chat History: {prepared_chat_history}")

        retriever_prompt = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                ("user", "대화에서 얻은 정보를 바탕으로 관련 문서를 검색하기 위한 쿼리를 생성해주세요.")
            ]
        )
        retriever_chain = LLMChain(llm=self.llm, prompt=retriever_prompt)
        retriever_results = retriever_chain.invoke(
            {
                "chat_history": prepared_chat_history,
                "input": query,
            }
        )
        retriever_results_content = (
            "\n".join([doc["content"] for doc in retriever_results]) if isinstance(retriever_results, list) else ""
        )
        context_with_documents = f"{context}\n{retriever_results_content}"
        logger.info(f"Combined context with documents: {context_with_documents}")

        document_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "아래 문맥을 사용하여 사용자의 질문에 한글로 답변해주세요. 문맥에서 최대한 많은 정보를 추출하고 필요하면 추론하세요:\n\n{context}"),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}")
            ]
        )
        document_chain = LLMChain(llm=self.llm, prompt=document_prompt)
        result = document_chain.invoke(
            {
                "chat_history": prepared_chat_history,
                "input": query,
                "context": context_with_documents,
            }
        )
        final_content = result.get("text", "") if isinstance(result, Dict) else ""
        logger.info(f"Extracted final content: {final_content}")

        if not final_content:
            logger.error("응답에 유효한 콘텐츠가 포함되어 있지 않음")
            return BLACKLIST_RESPONSE

        chat_history.insert(0, {"role": "assistant", "content": final_content.strip()})
        chat_history.insert(0, {"role": "user", "content": query})

        if final_content.strip() == BLACKLIST_RESPONSE:
            return final_content.strip()

        follow_up_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", f"다음 답변을 바탕으로: '{final_content.strip()}'"),
                ("user", "위의 내용을 바탕으로 추가로 궁금해할 수 있는 질문을 두 개만 생성하여 "
                         "번호를 붙여주세요. 다만, 답변이 명확하지 않은 경우, 또는 답변을 하지 못했을 경우에는 후속 질문을 생성하지 말아주세요.")
            ]
        )
        follow_up_chain = LLMChain(llm=self.llm, prompt=follow_up_prompt)
        follow_up_result = follow_up_chain.invoke(
            {
                "chat_history": prepared_chat_history,
                "context": context_with_documents,
                "input": query,
            }
        )
        follow_up_question = follow_up_result.get("text", "").strip() if isinstance(follow_up_result, Dict) else ""
        logger.info(f"Follow-up Question: {follow_up_question}")

        if follow_up_question:
            follow_up_questions = follow_up_question.split('\n')[:2]
            follow_up_questions = [q.strip() for q in follow_up_questions if q.strip()]

            if follow_up_questions:
                follow_up_list = "\n".join(follow_up_questions)
                combined_response = f"{final_content.strip()}\n\n추가로 다음에 대해 알아보시겠습니까?\n{follow_up_list}"
            else:
                combined_response = final_content.strip()
        else:
            combined_response = final_content.strip()

        chat_history.insert(0, {"role": "assistant", "content": combined_response})
        return combined_response
