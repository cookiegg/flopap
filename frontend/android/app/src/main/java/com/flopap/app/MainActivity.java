package com.flopap.app;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

import com.flopap.app.audio.PaperAudioPlugin;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        // Register the PaperAudio plugin
        registerPlugin(PaperAudioPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
