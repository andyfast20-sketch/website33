import re
import os
from datetime import datetime

def analyze_last_call():
    """Analyze the most recent call from logs"""
    print("\n" + "="*80)
    print("📊 ANALYZING LAST PHONE CALL")
    print("="*80 + "\n")
    
    try:
        # Read log file
        # Prefer explicitly set LOG_FILE, otherwise try common defaults.
        log_file = os.getenv('LOG_FILE')
        if log_file and os.path.exists(log_file):
            pass
        else:
            log_file = None
            for candidate in ('server.log', 'server_startup.log', 'server_log.txt'):
                if os.path.exists(candidate):
                    log_file = candidate
                    break

        if not log_file:
            print("❌ Log file not found. Set LOG_FILE or generate logs.")
            return
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
        
        # Find all call UUIDs
        call_pattern = r'\[([a-f0-9-]{36})\]'
        calls = list(set(re.findall(call_pattern, log_content)))
        
        if not calls:
            print("❌ No calls found in logs.")
            print("   Make a test call first, then run diagnostics.\n")
            return
        
        # Get the last call
        last_call = calls[-1]
        print(f"📞 Call UUID: {last_call}")
        print("="*80 + "\n")
        
        # Extract lines for this call
        call_lines = [line for line in log_content.split('\n') if last_call in line]
        
        # Parse events with timestamps
        events = []
        for line in call_lines:
            timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
            if not timestamp_match:
                continue
            
            ts_str = timestamp_match.group(1)
            try:
                ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S,%f')
            except:
                continue
            
            # Capture key events
            if 'VAD:' in line or 'VAD silence' in line:
                match = re.search(r'silence=(\d+)ms', line)
                if match:
                    events.append(('vad_configured', ts, int(match.group(1)), line))
            elif 'Text delta:' in line:
                match = re.search(r'Text delta: (\d+) chars', line)
                if match:
                    events.append(('text_delta', ts, int(match.group(1)), line))
            elif 'INSTANT:' in line or 'EARLY GEN' in line:
                match = re.search(r'started at (\d+) chars', line)
                if match:
                    events.append(('early_gen', ts, int(match.group(1)), line))
            elif 'TTS' in line or ('generated' in line and 'ms' in line):
                match = re.search(r'in (\d+)ms', line)
                if match:
                    events.append(('tts', ts, int(match.group(1)), line))
            elif 'TEXT DONE' in line:
                events.append(('text_done', ts, None, line))
        
        if not events:
            print("⚠️  No timing events found for this call.\n")
            print("Recent call activity:")
            for line in call_lines[-20:]:
                print(f"  {line}")
            return
        
        # Display timeline
        print("⏱️  EVENT TIMELINE")
        print("="*80 + "\n")
        
        start_time = events[0][1]
        timing_data = {
            'vad_ms': None,
            'tts_ms': None,
            'early_gen': False,
            'early_gen_chars': 0,
            'text_chars': []
        }
        
        for event_type, timestamp, value, line in events:
            elapsed = (timestamp - start_time).total_seconds() * 1000
            
            if event_type == 'vad_configured':
                print(f"+{elapsed:6.0f}ms | 🎤 VAD configured: {value}ms silence detection")
                timing_data['vad_ms'] = value
            elif event_type == 'text_delta':
                print(f"+{elapsed:6.0f}ms | 📝 Text received: {value} characters")
                timing_data['text_chars'].append(value)
            elif event_type == 'early_gen':
                print(f"+{elapsed:6.0f}ms | ⚡ EARLY GENERATION STARTED at {value} chars!")
                timing_data['early_gen'] = True
                timing_data['early_gen_chars'] = value
            elif event_type == 'text_done':
                print(f"+{elapsed:6.0f}ms | ✅ Text generation complete")
            elif event_type == 'tts':
                print(f"+{elapsed:6.0f}ms | 🔊 TTS: {value}ms")
                timing_data['tts_ms'] = value
        
        # Analysis
        print("\n" + "="*80)
        print("📊 PERFORMANCE ANALYSIS")
        print("="*80 + "\n")
        
        issues = []
        recommendations = []
        
        # Check VAD
        if timing_data['vad_ms']:
            if timing_data['vad_ms'] < 300:
                print(f"⚠️  VAD: {timing_data['vad_ms']}ms - TOO FAST (may interrupt user)")
                issues.append(f"VAD silence detection is {timing_data['vad_ms']}ms - this can cause AI to talk over user")
                recommendations.append("Increase VAD silence_duration_ms to 400-500ms")
            elif timing_data['vad_ms'] > 600:
                print(f"⚠️  VAD: {timing_data['vad_ms']}ms - TOO SLOW (user waits too long)")
                issues.append(f"VAD silence detection is {timing_data['vad_ms']}ms - this makes response feel slow")
                recommendations.append("Decrease VAD silence_duration_ms to 400ms")
            else:
                print(f"✅ VAD: {timing_data['vad_ms']}ms - GOOD")
        
        # Check early generation
        if timing_data['early_gen']:
            print(f"✅ Early Generation: ACTIVE at {timing_data['early_gen_chars']} chars")
        else:
            print(f"❌ Early Generation: NOT TRIGGERED")
            issues.append("Early audio generation did not trigger - TTS only started after full text")
            recommendations.append("Enable early audio generation to start TTS while OpenAI is still generating text")
        
        # Check TTS speed
        if timing_data['tts_ms']:
            if timing_data['tts_ms'] > 1200:
                print(f"❌ TTS Speed: {timing_data['tts_ms']}ms - VERY SLOW")
                issues.append(f"TTS generation takes {timing_data['tts_ms']}ms - this is the main bottleneck")
                recommendations.append("Consider switching to a faster TTS provider (OpenAI built-in voice or ElevenLabs)")
            elif timing_data['tts_ms'] > 700:
                print(f"⚠️  TTS Speed: {timing_data['tts_ms']}ms - SLOW")
                issues.append(f"TTS generation takes {timing_data['tts_ms']}ms")
                recommendations.append("TTS is slower than optimal - consider OpenAI's built-in voice")
            else:
                print(f"✅ TTS Speed: {timing_data['tts_ms']}ms - GOOD")
        
        print("\n" + "="*80 + "\n")
        
        if issues:
            print("🔴 ISSUES FOUND:\n")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            
            print("\n💡 RECOMMENDATIONS:\n")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print("✅ No major issues detected!")
        
        print("\n" + "="*80 + "\n")
        
        # Summary
        if timing_data['tts_ms']:
            total_estimated = (timing_data['vad_ms'] or 400) + 300 + timing_data['tts_ms']
            print(f"📈 ESTIMATED TOTAL RESPONSE TIME: ~{total_estimated}ms ({total_estimated/1000:.1f} seconds)")
            print(f"   - VAD wait: {timing_data['vad_ms'] or 400}ms")
            print(f"   - OpenAI text: ~300ms")
            print(f"   - TTS generation: {timing_data['tts_ms']}ms")
            if timing_data['early_gen']:
                print(f"   - Early generation helped reduce perceived latency!")
        
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        print(f"\n{traceback.format_exc()}")

if __name__ == "__main__":
    analyze_last_call()
