package com.example.piganapp

import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class WatchTutorialActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_watch_tutorial)

        supportActionBar?.title = "Watch Tutorial"

        val webView: WebView = findViewById(R.id.webView)
        webView.webViewClient = WebViewClient()
        webView.settings.javaScriptEnabled = true

        // Replace with your actual YouTube video URL
        val tutorialUrl = "https://youtu.be/HWAT0OzGwg8"
        webView.loadUrl(tutorialUrl)
    }
}