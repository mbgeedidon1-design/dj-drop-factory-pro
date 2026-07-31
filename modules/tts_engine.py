@@
@@
@@
-        result = subprocess.run([self.espeak_cmd, "-v", voice, "-s", str(speed), "-p", str(pitch), "-a", "200", "-f", txt_path, "-w", wav_path], capture_output=True, text=True, timeout=30)
-            if result.returncode != 0:
-                raise RuntimeError(f"eSpeak error: {result.stderr}")
-            if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
-                raise RuntimeError("Empty audio output")
-
-            if self.ffmpeg_available:
-                tempo = max(0.5, min(2.0, speed / 175))
-                subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-af", f"atempo={tempo:.2f}", "-ar", str(Config.AUDIO_SAMPLE_RATE), "-ac", str(Config.AUDIO_CHANNELS), "-b:a", Config.AUDIO_BITRATE, output_path], capture_output=True)
-                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
-                    os.remove(wav_path)
-                else:
-                    os.rename(wav_path, output_path)
-            else:
-                os.rename(wav_path, output_path)
-
-            return {"filename": output_filename, "path": output_path, "voice": f"espeak-{voice}", "engine": "espeak-ng"}
+        # choose amplitude used with eSpeak (keeps value for returning to API)
+        amplitude = 200
+
+        result = subprocess.run(
+            [self.espeak_cmd, "-v", voice, "-s", str(speed), "-p", str(pitch), "-a", str(amplitude), "-f", txt_path, "-w", wav_path],
+            capture_output=True,
+            text=True,
+            timeout=30
+        )
+        if result.returncode != 0:
+            raise RuntimeError(f"eSpeak error: {result.stderr}")
+        if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
+            raise RuntimeError("Empty audio output")
+
+        if self.ffmpeg_available:
+            tempo = max(0.5, min(2.0, speed / 175))
+            subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-af", f"atempo={tempo:.2f}", "-ar", str(Config.AUDIO_SAMPLE_RATE), "-ac", str(Config.AUDIO_CHANNELS), "-b:a", Config.AUDIO_BITRATE, output_path], capture_output=True)
+            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
+                os.remove(wav_path)
+            else:
+                os.rename(wav_path, output_path)
+        else:
+            os.rename(wav_path, output_path)
+
+        # return rate/pitch/volume so the API response can include them
+        return {
+            "filename": output_filename,
+            "path": output_path,
+            "voice": f"espeak-{voice}",
+            "engine": "espeak-ng",
+            "rate": speed,
+            "pitch": pitch,
+            "volume": amplitude
+        }
