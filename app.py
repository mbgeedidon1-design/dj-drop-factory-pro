@@
-        return jsonify({
-            "success": True,
-            "script": script,
-            "download_url": f"/static/generated/{os.path.basename(final_path)}",
-            "image_url": f"/static/generated/{cover_filename}" if cover_filename else None,
-            "project": drop_id,
-            "offline": not audio_processor.ffmpeg_available,
-            "voice_used": tts_result['voice'],
-            "processing": {
-                "rate": tts_result['rate'],
-                "pitch": tts_result['pitch'],
-                "volume": tts_result['volume'],
-                "fx_mode": fx_mode
-            }
-        })
+        return jsonify({
+            "success": True,
+            "script": script,
+            "download_url": f"/static/generated/{os.path.basename(final_path)}",
+            "image_url": f"/static/generated/{cover_filename}" if cover_filename else None,
+            "project": drop_id,
+            "offline": not audio_processor.ffmpeg_available,
+            "voice_used": tts_result.get('voice'),
+            "processing": {
+                "rate": tts_result.get('rate'),
+                "pitch": tts_result.get('pitch'),
+                "volume": tts_result.get('volume'),
+                "fx_mode": fx_mode
+            }
+        })
@@
