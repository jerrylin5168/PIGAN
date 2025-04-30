package com.example.piganapp

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class ReadTutorialActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_read_tutorial)

        // Optional: set toolbar title or back button
        supportActionBar?.title = "Read Tutorial"
    }
}
