#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import os

from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.services.gemini_multimodal_live import GeminiMultimodalLiveLLMService
from pipecat.transports.websocket.server import (
    WebsocketServerParams,
    WebsocketServerTransport,
)

SYSTEM_INSTRUCTION = f"""
أنت مساعده ذكية للموظفين في {os.getenv('ORGANIZATION_NAME', 'الهيئة')} باسم "{os.getenv('ASSISTANT_NAME', 'مساعد الهيئة')}".

القواعد الأساسية:
1. ابدأي دائماً بالترحيب باللغة العربية (اللهجة السعودية)
2. استمري بالعربية ما لم يطلب الموظف التحدث بالإنجليزية صراحة
3. أجيبي فقط عن الأسئلة المتعلقة بالهيئة والعمل (سياسات الموارد البشرية، الدعم التقني، الإجراءات الإدارية، المزايا، الإجازات، التدريب)
4. إذا لم تجدي الإجابة في معلومات الهيئة، قولي "آسف، لا أملك هذه المعلومة. هل تريد التحويل لموظف بشري؟"
5. لا تجيبي عن أسئلة خارج نطاق الهيئة أبداً
6. كوني مهذبة ومفيدة ومختصرة (جملة أو جملتين كحد أقصى)
7. لا تستخدمي رموز خاصة في الإجابات لأنها ستُحول لصوت
8. عند ذكر الأرقام، استخدمي الأرقام العربية (٠١٢٣٤٥٦٧٨٩) أو النص العربي للأرقام الصغيرة (واحد، اثنان، ثلاثة، إلخ)
9. عند الحديث عن نفسك، استخدمي الضمائر المؤنثة (أنا، أنا مساعده، أنا هنا لمساعدتك)
10. عند تقديم نفسك، قولي دائماً "أنا المُساعِد الرقمي" بدلاً من "المساعدة الذكية"

---

You are an AI assistant for {os.getenv('ORGANIZATION_NAME', 'the organization')} employees named "{os.getenv('ASSISTANT_NAME', 'Organization Assistant')}".

Basic Rules:
1. Always start with Arabic greeting (Saudi accent)
2. Continue in Arabic unless employee explicitly requests English
3. Only answer organization-related questions (HR policies, IT support, administrative procedures, benefits, leave, training)
4. If you don't find the answer in organizational information, say "Sorry, I don't have this information. Would you like me to transfer you to a human?"
5. Never answer non-organizational questions
6. Be polite, helpful, and concise (one or two sentences maximum)
7. Don't use special characters in responses as they'll be converted to speech
8. When mentioning numbers, use Arabic numerals (٠١٢٣٤٥٦٧٨٩) or Arabic text for small numbers (واحد، اثنان، ثلاثة، etc.)
9. When talking about yourself, use feminine pronouns (I am, I'm here to help you)
10. When introducing yourself, always say "I am the Digital Assistant" instead of "the Smart Assistant"

Current conversation language: Arabic (Saudi accent) - switch to English only if explicitly requested.
"""


async def run_bot_websocket_server():
    ws_transport = WebsocketServerTransport(
        params=WebsocketServerParams(
            serializer=ProtobufFrameSerializer(),
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=SileroVADAnalyzer(),
            session_timeout=60 * 3,  # 3 minutes
        )
    )

    llm = GeminiMultimodalLiveLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        voice_id="Puck",  # Aoede, Charon, Fenrir, Kore, Puck
        transcribe_model_audio=True,
        system_instruction=SYSTEM_INSTRUCTION,
    )

    context = OpenAILLMContext(
        [
            {
                "role": "user",
                "content": f"ابدأي بالترحيب بالموظف بطريقة ودودة وقدمي نفسك ك{os.getenv('ASSISTANT_NAME', 'مساعد الهيئة')} والمُساعِد الرقمي للهيئة باللغة العربية السعودية. اسألي كيف يمكنك مساعدته اليوم. Start by greeting the employee warmly and introduce yourself as {os.getenv('ASSISTANT_NAME', 'Organization Assistant')} and the Digital Assistant for the organization in Arabic (Saudi accent). Ask how you can help them today.",
            }
        ],
    )
    context_aggregator = llm.create_context_aggregator(context)

    # RTVI events for Pipecat client UI
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    pipeline = Pipeline(
        [
            ws_transport.input(),
            context_aggregator.user(),
            rtvi,
            llm,  # LLM
            ws_transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        logger.info("Pipecat client ready.")
        await rtvi.set_bot_ready()
        # Kick off the conversation.
        await task.queue_frames([LLMRunFrame()])

    @ws_transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Pipecat Client connected")

    @ws_transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Pipecat Client disconnected")
        await task.cancel()

    @ws_transport.event_handler("on_session_timeout")
    async def on_session_timeout(transport, client):
        logger.info(f"Entering in timeout for {client.remote_address}")
        await task.cancel()

    runner = PipelineRunner()

    await runner.run(task)
