// BAML configuration for botex structured parsing
generator BoundaryML {
  output_type python/pydantic
  output_dir "../baml_client"
}

// Client configuration for DeepSeek (using OpenAI-compatible API)
client<llm> DeepSeekClient {
  provider openai
  options {
    base_url "https://api.deepseek.com"
    model "deepseek-chat"
    api_key env.DEEPSEEK_API_KEY
  }
}

// Schema definitions for botex responses
class BotexAnswer {
  reason string
  answer (string | int | bool)
}

class BotexResponse {
  answers map<string, BotexAnswer>
  summary string
  confused bool
}

// Function to parse unstructured LLM responses into structured format
function ParseBotexResponse(
  raw_response: string,
  expected_schema: string
) -> BotexResponse {
  client DeepSeekClient
  prompt #"
    You are a response parser. Extract structured information from this raw response.
    
    Raw response: {{raw_response}}
    Expected schema: {{expected_schema}}
    
    Parse the raw response into the exact format specified by the schema.
    Return only valid JSON matching the schema.
    
    Requirements:
    - Preserve all question IDs exactly
    - Match expected answer types (string/int/bool)  
    - Brief but clear reasoning
    - Set confused=false unless response shows genuine confusion
    
    Return ONLY the JSON object.
  "#
}