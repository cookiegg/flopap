package com.flopap.app;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import android.util.Log;

@CapacitorPlugin(name = "Media3Player")
public class Media3PlayerPlugin extends Plugin {

    private static final String TAG = "Media3Player";

    @Override
    public void load() {
        Log.d(TAG, "Media3Player plugin loaded");
    }

    @PluginMethod
    public void playAudio(PluginCall call) {
        String url = call.getString("url");
        String title = call.getString("title", "Unknown");
        String artist = call.getString("artist", "Unknown Artist");

        Log.d(TAG, "Play requested: " + url);

        if (url == null) {
            call.reject("URL is required");
            return;
        }

        // For now, just log and resolve
        call.resolve();
    }

    @PluginMethod
    public void pause(PluginCall call) {
        Log.d(TAG, "Pause requested");
        call.resolve();
    }

    @PluginMethod
    public void stop(PluginCall call) {
        Log.d(TAG, "Stop requested");
        call.resolve();
    }

    @PluginMethod
    public void isPlaying(PluginCall call) {
        Log.d(TAG, "isPlaying requested");
        JSObject ret = new JSObject();
        ret.put("isPlaying", false);
        call.resolve(ret);
    }
}
