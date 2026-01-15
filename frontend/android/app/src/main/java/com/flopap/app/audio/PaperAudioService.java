package com.flopap.app.audio;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.content.Intent;
import android.os.Binder;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.PowerManager;
import android.util.Log;
import androidx.annotation.Nullable;
import androidx.annotation.OptIn;
import androidx.media3.common.AudioAttributes;
import androidx.media3.common.C;
import androidx.media3.common.MediaItem;
import androidx.media3.common.MediaMetadata;
import androidx.media3.common.Player;
import androidx.media3.common.util.UnstableApi;
import androidx.media3.common.util.Util;
import androidx.media3.datasource.DataSource;
import androidx.media3.datasource.DefaultDataSource;
import androidx.media3.datasource.DefaultHttpDataSource;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory;
import androidx.media3.session.DefaultMediaNotificationProvider;
import androidx.media3.session.MediaSession;
import androidx.media3.session.MediaSessionService;
import java.util.HashMap;
import java.util.Map;

public class PaperAudioService extends MediaSessionService {

    private static final String TAG = "PaperAudioService";
    private static final String CHANNEL_ID = "flopap_audio_channel";
    
    private MediaSession mediaSession = null;
    private ExoPlayer player;
    private PowerManager.WakeLock wakeLock;
    private final IBinder binder = new LocalBinder();
    private Handler mainHandler = new Handler(Looper.getMainLooper());

    // Configuration
    private boolean isAutoPlay = true; // Default to continuous play

    public class LocalBinder extends Binder {
        public PaperAudioService getService() {
            return PaperAudioService.this;
        }
    }

    @OptIn(markerClass = UnstableApi.class)
    @Override
    public void onCreate() {
        super.onCreate();
        Log.i(TAG, "Creating PaperAudioService");

        // 0. Create Notification Channel (required for Android 8+)
        createNotificationChannel();
        
        // 1. Acquire WakeLock
        acquireWakeLock();

        // 2. Configure Player with Headers (403 Fix)
        initializePlayer();

        // 3. Create MediaSession
        mediaSession = new MediaSession.Builder(this, player).build();
        
        // 4. Set up foreground service notification for background playback
        // Use Media3's built-in DefaultMediaNotificationProvider
        setMediaNotificationProvider(
            new DefaultMediaNotificationProvider.Builder(this)
                .setChannelId(CHANNEL_ID)
                .build()
        );
        
        Log.i(TAG, "PaperAudioService created with foreground notification support");
    }
    
    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "论文音频播放",
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("用于后台播放论文音频");
            channel.setShowBadge(false);
            
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
            Log.i(TAG, "Notification channel created: " + CHANNEL_ID);
        }
    }

    private void acquireWakeLock() {
        try {
            PowerManager powerManager = (PowerManager) getSystemService(Context.POWER_SERVICE);
            wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "Flopap:PaperAudioService");
            wakeLock.acquire(12 * 60 * 60 * 1000L); // 12 hours timeout as safety
            Log.i(TAG, "WakeLock acquired");
        } catch (Exception e) {
            Log.e(TAG, "Failed to acquire WakeLock", e);
        }
    }

    @OptIn(markerClass = UnstableApi.class)
    private void initializePlayer() {
        // Headers for CDN
        Map<String, String> defaultRequestProperties = new HashMap<>();
        defaultRequestProperties.put("Referer", "https://flopap.com");

        DataSource.Factory dataSourceFactory = new DefaultDataSource.Factory(
            this,
            new DefaultHttpDataSource.Factory()
                .setUserAgent(Util.getUserAgent(this, "Flopap"))
                .setDefaultRequestProperties(defaultRequestProperties)
        );

        player = new ExoPlayer.Builder(this)
            .setMediaSourceFactory(new DefaultMediaSourceFactory(dataSourceFactory))
            .setAudioAttributes(
                new AudioAttributes.Builder()
                    .setUsage(C.USAGE_MEDIA)
                    .setContentType(C.AUDIO_CONTENT_TYPE_SPEECH)
                    .build(),
                true  // handleAudioFocus
            )
            .setWakeMode(C.WAKE_MODE_NETWORK)
            .setHandleAudioBecomingNoisy(true)  // Pause when headphones disconnected
            .build();

        // Listeners for AutoPlay check logic is now handled by setPauseAtEndOfMediaItems
        // We can still listen for generic events if needed, but the manual pause logic is removed.
    }

    // --- Public API for Plugin ---

    @OptIn(markerClass = UnstableApi.class)
    public void setPlaylist(java.util.List<MediaItem> items, String startId) {
        mainHandler.post(() -> {
            if (player == null) return;
            player.setMediaItems(items);
            
            int startIndex = 0;
            if (startId != null) {
                for (int i = 0; i < items.size(); i++) {
                    if (startId.equals(items.get(i).mediaId)) {
                        startIndex = i;
                        break;
                    }
                }
            }
            
            player.seekTo(startIndex, 0);
            player.prepare();
            player.play();
            
            Log.i(TAG, "Playlist set with " + items.size() + " items, starting at " + startIndex);
        });
    }

    public void appendItems(java.util.List<MediaItem> items) {
        mainHandler.post(() -> {
            if (player == null) return;
            player.addMediaItems(items);
            Log.i(TAG, "Appended " + items.size() + " items, total: " + player.getMediaItemCount());
        });
    }

    public void playId(String id) {
        mainHandler.post(() -> {
            if (player == null) return;
            for (int i = 0; i < player.getMediaItemCount(); i++) {
                MediaItem item = player.getMediaItemAt(i);
                if (item.mediaId.equals(id)) {
                    player.seekTo(i, 0);
                    player.play();
                    return;
                }
            }
        });
    }

    public void removeItem(String id) {
        mainHandler.post(() -> {
            if (player == null) return;
            for (int i = 0; i < player.getMediaItemCount(); i++) {
                MediaItem item = player.getMediaItemAt(i);
                if (item.mediaId.equals(id)) {
                    player.removeMediaItem(i);
                    return;
                }
            }
        });
    }

    public void pause() {
        mainHandler.post(() -> {
            if (player != null) player.pause();
        });
    }

    public void resume() {
        mainHandler.post(() -> {
            if (player != null) player.play();
        });
    }
    
    public void seek(long positionMs) {
        mainHandler.post(() -> {
            if (player != null) player.seekTo(positionMs);
        });
    }
    
    public void setAutoPlay(boolean autoPlay) {
        mainHandler.post(() -> {
            this.isAutoPlay = autoPlay;
            if (player != null) {
                player.setPauseAtEndOfMediaItems(!autoPlay);
            }
            Log.i(TAG, "AutoPlay set to: " + autoPlay);
        });
    }
    
    public Player getPlayer() {
        return player;
    }

    // --- Lifecycle ---

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        super.onStartCommand(intent, flags, startId);
        return START_NOT_STICKY; 
    }

    @Nullable
    @Override
    public MediaSession onGetSession(MediaSession.ControllerInfo controllerInfo) {
        return mediaSession;
    }

    @Override
    public IBinder onBind(Intent intent) {
        // If binding from Plugin (Local), return Binder.
        // If binding from System (MediaSessionService), super.onBind handles it via Intent Action.
        if ("com.flopap.app.audio.BIND".equals(intent.getAction())) {
            return binder;
        }
        return super.onBind(intent);
    }

    @Override
    public void onDestroy() {
        Log.i(TAG, "Destroying PaperAudioService");
        // Use handler to ensure we release on the same thread we created/accessed
        new Handler(Looper.getMainLooper()).post(() -> {
            if (wakeLock != null && wakeLock.isHeld()) {
                wakeLock.release();
            }
            if (mediaSession != null) {
                mediaSession.release();
                mediaSession = null;
            }
            if (player != null) {
                player.release();
                player = null;
            }
        });
        super.onDestroy();
    }
}
