import asyncio
import websockets
import json
import base64
import tempfile
import os
import pygame
import time

# API_KEY should be loaded from environment variable or config, not hardcoded
import os
API_KEY = os.getenv('ELEVENLABS_API_KEY', '')  # Set in .env file or environment
# Hindi Female Voice with Empathy - Rachel (works excellently with Hindi using eleven_multilingual_v2)
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Rachel - Female, Empathetic, Multilingual Hindi support

# Hindi Voice Configuration Options
HINDI_VOICES = {
    "rachel": {
        "id": "21m00Tcm4TlvDq8ikWAM",
        "name": "Rachel", 
        "description": "Empathetic, warm female voice - excellent for Hindi",
        "settings": {
            "speed": 0.9,
            "stability": 0.7,
            "similarity_boost": 0.9,
            "style": 0.2,
            "use_speaker_boost": True
        }
    },
    "aria": {
        "id": "9BWtsMINqrJLrRacOBM5",
        "name": "Aria",
        "description": "Expressive, dynamic female voice - great for emotional Hindi content",
        "settings": {
            "speed": 0.85,
            "stability": 0.75,
            "similarity_boost": 0.85,
            "style": 0.25,
            "use_speaker_boost": True
        }
    },
    "serena": {
        "id": "DH3QnTgOXqjx6A4BCWM4", 
        "name": "Serena",
        "description": "Pleasant, gentle female voice - perfect for calm Hindi narration",
        "settings": {
            "speed": 0.95,
            "stability": 0.8,
            "similarity_boost": 0.9,
            "style": 0.15,
            "use_speaker_boost": True
        }
    }
}

def get_hindi_voice_config(voice_name="rachel"):
    """
    Get voice configuration for Hindi synthesis
    
    Args:
        voice_name (str): Voice name from HINDI_VOICES ("rachel", "aria", "serena")
    
    Returns:
        dict: Voice configuration with ID and settings
    """
    if voice_name.lower() not in HINDI_VOICES:
        print(f"⚠️ Voice '{voice_name}' not found. Using default 'rachel'")
        voice_name = "rachel"
    
    config = HINDI_VOICES[voice_name.lower()]
    print(f"🎭 Using {config['name']}: {config['description']}")
    return config

def play_audio_python(audio_data, filename=None):
    """
    Play audio data using pygame (Python-only audio playback)
    
    Args:
        audio_data (bytes): MP3 audio data
        filename (str): Optional filename for identification
    """
    if filename is None:
        filename = "temp_audio.mp3"
    
    try:
        # Initialize pygame mixer
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024)
        pygame.mixer.init()
        
        # Create a temporary file for pygame
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        
        print(f"🔊 Playing audio in Python: {filename}")
        
        # Load and play the audio
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        print("✅ Audio playback completed")
        
        # Clean up
        pygame.mixer.quit()
        
        # Optional: Remove temp file after playback
        try:
            os.remove(temp_path)
        except:
            pass  # Don't fail if we can't remove temp file
        
        return True
        
    except Exception as e:
        print(f"❌ Error playing audio with pygame: {e}")
        return False

async def play_audio_async(audio_data, filename=None):
    """
    Async wrapper for Python audio playback
    """
    return await asyncio.get_event_loop().run_in_executor(None, play_audio_python, audio_data, filename)

def play_audio_chunk(audio_chunk, chunk_number):
    """
    Play individual audio chunks for real-time streaming playback
    """
    try:
        temp_filename = f"chunk_{chunk_number}.mp3"
        temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
        
        with open(temp_path, "wb") as f:
            f.write(audio_chunk)
        
        # Initialize a separate mixer instance for chunk playback
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Play the chunk
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()
        
        # Let it play for a short time before returning
        time.sleep(0.1)
        
        return True
        
    except Exception as e:
        print(f"❌ Error playing audio chunk {chunk_number}: {e}")
        return False

async def text_to_speech_stream():
    """
    Stream text-to-speech using ElevenLabs WebSocket API
    """
    # WebSocket URL for ElevenLabs streaming TTS
    uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream-input"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to ElevenLabs WebSocket")
            
            # Initialize connection with voice settings optimized for Hindi with empathy
            init_message = {
                "text": " ",
                "voice_settings": {
                    "speed": 0.9,         # Slightly slower for clearer Hindi pronunciation
                    "stability": 0.7,     # Higher stability for consistent Hindi accent
                    "similarity_boost": 0.9,  # Higher similarity for natural Hindi flow
                    "style": 0.2,         # Adds empathy and emotional expression
                    "use_speaker_boost": True  # Enhanced voice clarity for Hindi
                },
                "model_id": "eleven_multilingual_v2",  # Best model for Hindi support
                "xi_api_key": API_KEY
            }
            
            await websocket.send(json.dumps(init_message))
            print("✓ Sent initialization message")
            
            # Send text chunks for streaming
            text_chunks = [
                "Hello there! ",
                "This is a streaming ",
                "text-to-speech demo ",
                "using ElevenLabs WebSocket API. ",
                "The audio is generated in real-time!"
            ]
            
            # Send text chunks
            for i, chunk in enumerate(text_chunks):
                message = {
                    "text": chunk,
                    "try_trigger_generation": i == len(text_chunks) - 1  # Trigger generation on last chunk
                }
                await websocket.send(json.dumps(message))
                print(f"📤 Sent text chunk: '{chunk.strip()}'")
                await asyncio.sleep(0.3)  # Small delay between chunks
            
            # Send final empty message to indicate end of text
            final_message = {"text": ""}
            await websocket.send(json.dumps(final_message))
            print("✓ Sent final message to complete generation")
            
            # Receive and process audio chunks
            audio_chunks = []
            total_bytes = 0
            
            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if "audio" in data and data["audio"] is not None:
                        # Decode base64 audio data
                        audio_data = base64.b64decode(data["audio"])
                        audio_chunks.append(audio_data)
                        total_bytes += len(audio_data)
                        print(f"🎵 Received audio chunk: {len(audio_data)} bytes (Total: {total_bytes} bytes)")
                        
                        # Show alignment data if available
                        if "normalizedAlignment" in data and data["normalizedAlignment"] is not None:
                            alignment = data["normalizedAlignment"]
                            chars = alignment.get("chars", [])
                            if chars:
                                current_text = "".join(chars)
                                print(f"   Alignment: '{current_text}'")
                    
                    if data.get("isFinal", False):
                        print("✓ Received final audio chunk")
                        break
                        
                except websockets.exceptions.ConnectionClosed:
                    print("❌ WebSocket connection closed")
                    break
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    break
            
            # Save combined audio to file
            if audio_chunks:
                combined_audio = b''.join(audio_chunks)
                
                output_file = "elevenlabs_output.mp3"
                with open(output_file, "wb") as f:
                    f.write(combined_audio)
                
                print(f"✅ Audio saved to '{output_file}' ({len(combined_audio)} bytes total)")
                
                # Play the audio
                await play_audio_async(combined_audio, output_file)
                
                return combined_audio
            else:
                print("❌ No audio data received")
                return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

async def convert_single_text(text, voice_id=None, voice_settings=None):
    """
    Convert a single text string to speech using WebSocket streaming
    
    Args:
        text (str): Text to convert to speech
        voice_id (str): Voice ID to use (optional)
        voice_settings (dict): Voice settings (optional)
    
    Returns:
        bytes: Audio data as MP3 bytes, or None if failed
    """
    if voice_id is None:
        voice_id = VOICE_ID
    
    if voice_settings is None:
        # Optimized settings for Hindi female voice with empathy
        voice_settings = {
            "speed": 0.9,         # Slightly slower for clearer Hindi pronunciation  
            "stability": 0.7,     # Higher stability for consistent Hindi accent
            "similarity_boost": 0.9,  # Higher similarity for natural Hindi flow
            "style": 0.2,         # Adds empathy and emotional expression
            "use_speaker_boost": True  # Enhanced voice clarity for Hindi
        }
    
    uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"🔗 Converting text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            # Send initialization message with full text, optimized settings, and multilingual model
            init_message = {
                "text": text,
                "voice_settings": voice_settings,
                "model_id": "eleven_multilingual_v2",  # Best model for Hindi support
                "xi_api_key": API_KEY
            }
            
            await websocket.send(json.dumps(init_message))
            
            # Send final empty message to trigger generation
            await websocket.send(json.dumps({"text": ""}))
            
            # Collect audio chunks
            audio_chunks = []
            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if "audio" in data and data["audio"] is not None:
                        audio_data = base64.b64decode(data["audio"])
                        audio_chunks.append(audio_data)
                        
                    if data.get("isFinal", False):
                        break
                        
                except (websockets.exceptions.ConnectionClosed, json.JSONDecodeError):
                    break
            
            combined_audio = b''.join(audio_chunks)
            
            if len(combined_audio) == 0:
                print("⚠️ ElevenLabs returned 0 bytes of audio. This might be due to:")
                print("   1. Free Tier usage disabled due to unusual activity detection")
                print("   2. VPN/Proxy triggering abuse detectors") 
                print("   3. Account restrictions or quota exceeded")
                print("   4. Consider upgrading to a paid plan or checking network settings")
            else:
                print(f"✅ Generated {len(combined_audio)} bytes of audio")
            
            return combined_audio
            
    except Exception as e:
        print(f"❌ Error converting text to speech: {e}")
        print("💡 If you're getting permission errors, check:")
        print("   - API key validity and permissions")
        print("   - Account status (Free Tier restrictions)")
        print("   - Network settings (VPN/Proxy issues)")
        return None

# Example usage functions
async def demo_streaming():
    """Demo the streaming functionality"""
    print("🚀 Starting ElevenLabs WebSocket Streaming TTS Demo...")
    await text_to_speech_stream()

async def demo_single_conversion():
    """Demo single text conversion"""
    print("🚀 Starting single text conversion demo...")
    
    text = "Hello! This is a single text conversion using ElevenLabs WebSocket API."
    audio_data = await convert_single_text(text)
    
    if audio_data:
        with open("single_conversion.mp3", "wb") as f:
            f.write(audio_data)
        print("✅ Single conversion saved to 'single_conversion.mp3'")
        
        # Play the audio
        await play_audio_async(audio_data, "single_conversion.mp3")

async def demo_hindi_conversion():
    """Demo with Hindi text conversion using optimized female voice with empathy"""
    print("🚀 Starting Hindi text conversion demo...")
    print("🎭 Using Rachel's voice - Female, Empathetic, Hindi-optimized")
    
    # Sample Hindi text with empathy
    hindi_texts = [
        "नमस्ते! मैं आपकी सहायता के लिए यहाँ हूँ।",  # Hello! I am here to help you.
        "आपका दिन कैसा जा रहा है? मुझे बताएं कि मैं आपकी कैसे मदद कर सकती हूँ।",  # How is your day going? Tell me how I can help you.
        "चिंता न करें, सब कुछ ठीक हो जाएगा। मैं आपके साथ हूँ।",  # Don't worry, everything will be fine. I am with you.
        "आपकी बात सुनकर मुझे बहुत खुशी हुई। आप बहुत अच्छे हैं।"  # I was very happy to hear from you. You are very good.
    ]
    
    for i, text in enumerate(hindi_texts, 1):
        print(f"\n🔗 Converting Hindi text {i}: '{text}'")
        
        audio_data = await convert_single_text(text)
        
        if audio_data:
            filename = f"hindi_demo_{i}.mp3"
            with open(filename, "wb") as f:
                f.write(audio_data)
            print(f"✅ Hindi audio saved to '{filename}'")
            
            # Play the audio
            await play_audio_async(audio_data, filename)
            
            # Small delay between samples
            await asyncio.sleep(2)
        else:
            print(f"❌ Failed to convert Hindi text {i}")

async def demo_custom_text():
    """Demo with custom text input"""
    print("🚀 Starting custom text conversion demo...")
    
    # Get text from user
    print("Enter the text you want to convert to speech:")
    text = input("> ")
    
    if not text.strip():
        print("❌ No text provided")
        return
    
    print(f"🔗 Converting: '{text[:50]}{'...' if len(text) > 50 else ''}'")
    
    audio_data = await convert_single_text(text)
    
    if audio_data:
        filename = "custom_text.mp3"
        with open(filename, "wb") as f:
            f.write(audio_data)
        print(f"✅ Audio saved to '{filename}'")
        
        # Play the audio
        await play_audio_async(audio_data, filename)

async def demo_voice_settings():
    """Demo with different voice settings"""
    print("🚀 Starting voice settings demo...")
    
    text = "This is a demonstration of different voice settings. Listen to how speed, stability, and similarity affect the voice."
    
    # Test different voice settings
    voice_variations = [
        {"speed": 0.5, "stability": 0.3, "similarity_boost": 0.9, "name": "slow_calm"},
        {"speed": 1.5, "stability": 0.7, "similarity_boost": 0.6, "name": "fast_energetic"},
        {"speed": 1.0, "stability": 0.9, "similarity_boost": 0.5, "name": "stable_natural"}
    ]
    
    for i, settings in enumerate(voice_variations):
        print(f"\n🎭 Testing voice variation {i+1}: {settings['name']}")
        print(f"   Speed: {settings['speed']}, Stability: {settings['stability']}, Similarity: {settings['similarity_boost']}")
        
        voice_config = {
            "speed": settings["speed"],
            "stability": settings["stability"], 
            "similarity_boost": settings["similarity_boost"]
        }
        
        audio_data = await convert_single_text(text, voice_settings=voice_config)
        
        if audio_data:
            filename = f"voice_{settings['name']}.mp3"
            with open(filename, "wb") as f:
                f.write(audio_data)
            print(f"✅ Audio saved to '{filename}'")
            
            # Play the audio
            await play_audio_async(audio_data, filename)
            
            # Small delay between variations
            await asyncio.sleep(1)

# Main execution
if __name__ == "__main__":
    print("ElevenLabs WebSocket TTS Implementation")
    print("=====================================")
    
    # Choose demo to run
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "single":
            asyncio.run(demo_single_conversion())
        elif mode == "custom":
            asyncio.run(demo_custom_text())
        elif mode == "hindi":
            asyncio.run(demo_hindi_conversion())
        elif mode == "voices":
            asyncio.run(demo_voice_settings())
        elif mode == "stream":
            asyncio.run(demo_streaming())
        else:
            print("❌ Unknown mode. Available modes:")
            print("   python eleven_websocket.py          - Streaming demo")
            print("   python eleven_websocket.py single   - Single text demo")
            print("   python eleven_websocket.py custom   - Custom text input")
            print("   python eleven_websocket.py hindi    - Hindi empathy demo")
            print("   python eleven_websocket.py voices   - Voice settings demo")
            print("   python eleven_websocket.py stream   - Streaming demo")
    else:
        asyncio.run(demo_streaming())