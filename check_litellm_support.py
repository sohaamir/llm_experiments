#!/usr/bin/env python3
"""
Check any litellm model support and capabilities
"""

import litellm
import json
import sys
import argparse
from pprint import pprint
import os
from dotenv import load_dotenv

# Load environment variables from botex.env
load_dotenv('botex.env')

def check_model_support(model):
    """Check what litellm reports for any given model"""
    
    print(f"🔍 Checking model support in litellm: {model}")
    print("=" * 80)
    
    print(f"\n📋 Model: {model}")
    print("-" * 60)
    
    try:
        # Check supported parameters
        print("✅ Supported OpenAI parameters:")
        params = litellm.get_supported_openai_params(model=model)
        print(f"   Total parameters: {len(params)}")
        print(f"   Parameters: {sorted(params)}")
        print(f"   response_format supported: {'response_format' in params}")
        
    except Exception as e:
        print(f"❌ Error getting supported params: {e}")
    
    try:
        # Check response schema support
        print("\n✅ Response schema support:")
        schema_support = litellm.supports_response_schema(model=model)
        print(f"   litellm.supports_response_schema(): {schema_support}")
        
    except Exception as e:
        print(f"❌ Error checking schema support: {e}")
    
    try:
        # Check if model exists in litellm's model registry
        print("\n✅ Model registry lookup:")
        model_info = litellm.get_model_info(model)
        print(f"   Model info found: {model_info is not None}")
        if model_info:
            print("\n   Full model information:")
            pprint(model_info, width=100)
            
            # Extract key botex-relevant info
            print(f"\n   🤖 BOTEX COMPATIBILITY SUMMARY:")
            print(f"   ├── Mode: {model_info.get('mode', 'Unknown')}")
            print(f"   ├── Provider: {model_info.get('litellm_provider', 'Unknown')}")
            print(f"   ├── Max tokens: {model_info.get('max_tokens', 'Unknown')}")
            print(f"   ├── Supports function calling: {model_info.get('supports_function_calling', 'Unknown')}")
            print(f"   ├── Supports response schema: {model_info.get('supports_response_schema', 'Unknown')}")
            print(f"   ├── Supports system messages: {model_info.get('supports_system_messages', 'Unknown')}")
            print(f"   └── Cost per 1M tokens: Input ${model_info.get('input_cost_per_token', 0) * 1000000:.2f}, Output ${model_info.get('output_cost_per_token', 0) * 1000000:.2f}")
            
    except Exception as e:
        print(f"❌ Error getting model info: {e}")
    
    # Try to determine provider detection
    try:
        print("\n✅ Provider detection:")
        if "/" not in model:
            provider = "openai"  # litellm default
        else:
            provider = model.split("/")[0]
        print(f"   Detected provider: {provider}")
        
        # Check provider-specific support
        provider_params = litellm.get_supported_openai_params(
            model=model, 
            custom_llm_provider=provider
        )
        print(f"   Provider-specific params count: {len(provider_params)}")
        print(f"   Provider-specific response_format: {'response_format' in provider_params}")
        
        provider_schema_support = litellm.supports_response_schema(
            model=model,
            custom_llm_provider=provider
        )
        print(f"   Provider-specific schema support: {provider_schema_support}")
        
    except Exception as e:
        print(f"❌ Error checking provider-specific support: {e}")
    
    # Final botex compatibility assessment
    try:
        params = litellm.get_supported_openai_params(model=model)
        schema_support = litellm.supports_response_schema(model=model)
        model_info = litellm.get_model_info(model)
        
        print(f"\n🎯 FINAL BOTEX COMPATIBILITY ASSESSMENT:")
        print(f"   ┌─────────────────────────────────────┐")
        
        # Check requirements
        has_response_format = 'response_format' in params
        has_schema_support = schema_support
        is_chat_mode = model_info and model_info.get('mode') == 'chat'
        
        print(f"   │ response_format parameter: {'✅ YES' if has_response_format else '❌ NO':<9} │")
        print(f"   │ Schema support:            {'✅ YES' if has_schema_support else '❌ NO':<9} │")
        print(f"   │ Chat mode:                 {'✅ YES' if is_chat_mode else '❌ NO':<9} │")
        
        # Final verdict
        is_compatible = has_response_format and has_schema_support and is_chat_mode
        print(f"   │                                     │")
        print(f"   │ BOTEX COMPATIBLE:          {'✅ YES' if is_compatible else '❌ NO':<9} │")
        print(f"   └─────────────────────────────────────┘")
        
        if not is_compatible:
            print(f"\n   ⚠️  COMPATIBILITY ISSUES:")
            if not has_response_format:
                print(f"      • Missing response_format parameter support")
            if not has_schema_support:
                print(f"      • Missing structured output schema support")
            if not is_chat_mode:
                print(f"      • Not a chat completion model (botex requires chat mode)")
        
    except Exception as e:
        print(f"❌ Error in final assessment: {e}")

def main():
    parser = argparse.ArgumentParser(description='Check litellm model compatibility for botex')
    parser.add_argument('model', nargs='?', help='Model name to check (e.g., gpt-4o, anthropic/claude-3-5-sonnet, groq/llama-3.1-70b-versatile)')
    
    args = parser.parse_args()
    
    if not args.model:
        # Interactive mode if no model provided
        print("🤖 LITELLM MODEL COMPATIBILITY CHECKER")
        print("=" * 50)
        print("Enter a model name to check its botex compatibility")
        print("Examples:")
        print("  • gpt-4o")
        print("  • anthropic/claude-3-5-sonnet-20241022")
        print("  • groq/llama-3.1-70b-versatile")
        print("  • deepseek/deepseek-chat")
        print("  • gemini/gemini-1.5-flash")
        print()
        
        model = input("Model name: ").strip()
        if not model:
            print("No model provided. Exiting.")
            sys.exit(1)
    else:
        model = args.model
    
    # Check the model
    check_model_support(model)
    
    print(f"\n💡 USAGE TIP:")
    print(f"   If this model is compatible, you can add it to your botex.env:")
    print(f"   PROVIDER_MODELS={model}")

if __name__ == "__main__":
    main()