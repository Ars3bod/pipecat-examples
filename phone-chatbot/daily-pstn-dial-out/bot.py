#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""simple_dialout.py.

Daily PSTN Dial-out Bot.
"""

import os
from typing import Any

from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.runner.types import RunnerArguments
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.daily.transport import DailyParams, DailyTransport

load_dotenv()


async def run_bot(transport: BaseTransport, handle_sigint: bool) -> None:
    """Run the voice bot with the given parameters."""

    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY", ""),
        voice_id="b7d50908-b17c-442d-ad8d-810c63997ed9",  # Use Helpful Woman voice by default
    )

    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

    # Initialize LLM context with system prompt
    messages = [
        {
            "role": "system",
            "content": (
                "You are a friendly phone assistant. Your responses will be read aloud, "
                "so keep them concise and conversational. Avoid special characters or "
                "formatting. Begin by greeting the caller and asking how you can help them today."
            ),
        },
    ]

    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    # ------------ RETRY LOGIC VARIABLES ------------
    max_retries = 5
    retry_count = 0
    dialout_successful = False

    async def attempt_dialout(dialout_params):
        """Attempt to start dialout with retry logic."""
        nonlocal retry_count, dialout_successful

        if retry_count < max_retries and not dialout_successful:
            retry_count += 1
            phone_number = dialout_params.get("phoneNumber", "unknown")
            logger.info(
                f"Attempting dialout (attempt {retry_count}/{max_retries}) to: {phone_number}"
            )
            await transport.start_dialout(dialout_params)
        else:
            logger.error(f"Maximum retry attempts ({max_retries}) reached. Giving up on dialout.")

    @transport.event_handler("on_joined")
    async def on_joined(transport, data):
        # Extract dialout settings from transport's body data
        body_data = getattr(transport, "_body_data", {})
        dialout_settings = body_data.get("dialout_settings", {})

        if not dialout_settings.get("phone_number"):
            logger.error("Dial-out phone number not found in the dial-out settings")
            return

        phone_number = dialout_settings["phone_number"]
        caller_id = dialout_settings.get("caller_id")

        # Build dialout parameters conditionally
        dialout_params = {"phoneNumber": phone_number}
        if caller_id:
            dialout_params["callerId"] = caller_id
            logger.debug(f"Including caller ID in dialout: {caller_id}")

        logger.debug(f"Dialout parameters: {dialout_params}")
        logger.debug(f"Dialout settings detected; starting dialout to number: {phone_number}")
        await attempt_dialout(dialout_params)

    @transport.event_handler("on_dialout_connected")
    async def on_dialout_connected(transport, data):
        logger.debug(f"Dial-out connected: {data}")

    @transport.event_handler("on_dialout_answered")
    async def on_dialout_answered(transport, data):
        nonlocal dialout_successful
        logger.debug(f"Dial-out answered: {data}")
        dialout_successful = True  # Mark as successful to stop retries
        # The bot will wait to hear the user before the bot speaks

    @transport.event_handler("on_dialout_error")
    async def on_dialout_error(transport, data: Any):
        logger.error(f"Dial-out error (attempt {retry_count}/{max_retries}): {data}")

        if retry_count < max_retries:
            # Get dialout params again for retry
            body_data = getattr(transport, "_body_data", {})
            dialout_settings = body_data.get("dialout_settings", {})
            phone_number = dialout_settings.get("phone_number")
            caller_id = dialout_settings.get("caller_id")

            dialout_params = {"phoneNumber": phone_number}
            if caller_id:
                dialout_params["callerId"] = caller_id

            logger.info(f"Retrying dialout")
            await attempt_dialout(dialout_params)
        else:
            logger.error(f"All {max_retries} dialout attempts failed. Stopping bot.")
            await task.cancel()

    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        logger.debug(f"First participant joined: {participant['id']}")

    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        logger.debug(f"Participant left: {participant}, reason: {reason}")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat Cloud."""
    # Body is always a dict (compatible with both local and Pipecat Cloud)
    body_data = runner_args.body
    room_url = body_data.get("room_url")
    token = body_data.get("token")
    dialout_settings = body_data.get("dialout_settings", {})

    if not dialout_settings.get("phone_number"):
        logger.error("Phone number is required in dialout_settings.")
        return None

    transport_params = DailyParams(
        api_url=os.getenv("DAILY_API_URL", "https://api.daily.co/v1"),
        api_key=os.getenv("DAILY_API_KEY", ""),
        audio_in_enabled=True,
        audio_out_enabled=True,
        video_out_enabled=False,
        vad_analyzer=SileroVADAnalyzer(),
    )

    transport = DailyTransport(
        room_url,
        token,
        "Simple Dial-out Bot",
        transport_params,
    )

    # Store body data in transport for access in event handlers
    transport._body_data = body_data

    await run_bot(transport, runner_args.handle_sigint)
