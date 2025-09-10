# Telnyx Voice Bot Examples

This repository contains examples of voice bots that integrate with Telnyx's Voice API using Pipecat. The examples demonstrate both inbound and outbound calling scenarios using Telnyx's TeXML and WebSocket streaming for real-time audio processing.

## Examples

### 🔽 [Inbound Calling](./inbound/)

Demonstrates how to handle incoming phone calls where users call your Telnyx number and interact with a voice bot.

### 🔼 [Outbound Calling](./outbound/)

Shows how to initiate outbound phone calls programmatically where your bot calls users.

## Architecture

Both examples use the same core architecture:

```
Phone Call ↔ Telnyx ↔ TeXML/WebSocket ↔ Pipecat ↔ AI Services
```

**Components:**

- **Telnyx**: Handles phone call routing and audio transport
- **TeXML**: XML-based call control and WebSocket streaming
- **Pipecat**: Audio processing pipeline and AI service orchestration
- **AI Services**: OpenAI (LLM), Deepgram (STT), Cartesia (TTS)

## Getting Help

- **Detailed Setup**: See individual README files in `inbound/` and `outbound/` directories
- **Pipecat Documentation**: [docs.pipecat.ai](https://docs.pipecat.ai)
- **Telnyx Documentation**: [developers.telnyx.com](https://developers.telnyx.com)
