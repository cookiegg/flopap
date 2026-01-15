package com.flopap.app.audio;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.net.Uri;
import android.os.IBinder;
import android.util.Log;
import androidx.annotation.Nullable;
import androidx.media3.common.MediaItem;
import androidx.media3.common.MediaMetadata;
import androidx.media3.common.Player;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONException;
import org.json.JSONObject;

@CapacitorPlugin(name = "PaperAudio")
public class PaperAudioPlugin extends Plugin {

    private PaperAudioService service;
    private boolean isBound = false;
    private static final String TAG = "PaperAudioPlugin";

    private final ServiceConnection connection = new ServiceConnection() {
        @Override
        public void onServiceConnected(ComponentName className, IBinder binder) {
            PaperAudioService.LocalBinder localBinder = (PaperAudioService.LocalBinder) binder;
            service = localBinder.getService();
            isBound = true;
            Log.i(TAG, "Service Bound");
            
            // Attach Listener for JS Events
            service.getPlayer().addListener(new Player.Listener() {
                @Override
                public void onMediaItemTransition(@Nullable MediaItem mediaItem, @Player.MediaItemTransitionReason int reason) {
                    if (mediaItem != null) {
                        JSObject ret = new JSObject();
                        ret.put("id", mediaItem.mediaId);
                        notifyListeners("onCurrentItemChanged", ret);
                    }
                }

                @Override
                public void onIsPlayingChanged(boolean isPlaying) {
                    JSObject ret = new JSObject();
                    ret.put("isPlaying", isPlaying);
                    notifyListeners("onPlaybackStateChanged", ret);
                }
            });
        }

        @Override
        public void onServiceDisconnected(ComponentName arg0) {
            isBound = false;
            service = null;
        }
    };

    @Override
    public void load() {
        Intent intent = new Intent(getContext(), PaperAudioService.class);
        intent.setAction("com.flopap.app.audio.BIND");
        getContext().bindService(intent, connection, Context.BIND_AUTO_CREATE);
        
        // Try to start service to keep it alive (Old behavior), but wrap in try-catch for Android 14+
        try {
            getContext().startService(intent);
        } catch (Exception e) {
            Log.e(TAG, "Failed to start service (Background restriction? Safe to ignore if bound)", e);
        }
    }

    @Override
    protected void handleOnDestroy() {
        if (isBound) {
            getContext().unbindService(connection);
            isBound = false;
        }
        super.handleOnDestroy();
    }

    @PluginMethod
    public void setPlaylist(PluginCall call) {
        if (!isBound || service == null) {
            call.reject("Audio Service not bound yet");
            return;
        }
        
        try {
            JSArray items = call.getArray("items");
            String startId = call.getString("startId");
            List<MediaItem> mediaItems = new ArrayList<>();
            
            for (int i = 0; i < items.length(); i++) {
                mediaItems.add(jsonToMediaItem(items.getJSONObject(i)));
            }
            
            service.setPlaylist(mediaItems, startId);
            call.resolve();
        } catch (JSONException e) {
            call.reject("Invalid JSON", e);
        }
    }

    @PluginMethod
    public void appendItems(PluginCall call) {
        if (!isBound || service == null) {
            call.reject("Audio Service not bound yet");
            return;
        }

        try {
            JSArray items = call.getArray("items");
            List<MediaItem> mediaItems = new ArrayList<>();

            for (int i = 0; i < items.length(); i++) {
                mediaItems.add(jsonToMediaItem(items.getJSONObject(i)));
            }

            service.appendItems(mediaItems);
            call.resolve();
        } catch (JSONException e) {
            call.reject("Invalid JSON", e);
        }
    }

    @PluginMethod
    public void playId(PluginCall call) {
        if (service != null) service.playId(call.getString("id"));
        call.resolve();
    }

    @PluginMethod
    public void removeItem(PluginCall call) {
        if (service != null) service.removeItem(call.getString("id"));
        call.resolve();
    }

    @PluginMethod
    public void pause(PluginCall call) {
        if (service != null) service.pause();
        call.resolve();
    }

    @PluginMethod
    public void resume(PluginCall call) {
        if (service != null) service.resume();
        call.resolve();
    }

    @PluginMethod
    public void seek(PluginCall call) {
        if (service != null) {
             Double time = call.getDouble("time");
             if (time != null) {
                 service.seek((long)(time * 1000));
             }
        }
        call.resolve();
    }

    @PluginMethod
    public void setAutoPlay(PluginCall call) {
        if (service != null) {
            Boolean autoPlay = call.getBoolean("autoPlay", true);
            service.setAutoPlay(autoPlay);
        }
        call.resolve();
    }

    private MediaItem jsonToMediaItem(JSONObject json) throws JSONException {
        String id = json.getString("id");
        String url = json.getString("url");
        String title = json.optString("title", "");
        String artist = json.optString("artist", "Flopap");
        String artwork = json.optString("artwork", "");

        MediaMetadata.Builder metaBtn = new MediaMetadata.Builder()
            .setTitle(title)
            .setArtist(artist);
            
        if (!artwork.isEmpty()) {
            metaBtn.setArtworkUri(Uri.parse(artwork));
        }

        return new MediaItem.Builder()
            .setUri(url)
            .setMediaId(id)
            .setMediaMetadata(metaBtn.build())
            .build();
    }
}
