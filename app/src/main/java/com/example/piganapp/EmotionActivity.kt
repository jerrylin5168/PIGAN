package com.example.piganapp

import android.content.Intent
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.Spinner
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.appcompat.app.AppCompatActivity
import com.google.firebase.auth.FirebaseAuth
import okhttp3.OkHttpClient
import okhttp3.ResponseBody
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class EmotionActivity : AppCompatActivity() {
    // define variables for buttons and spinners (dropdowns)
    private lateinit var spinner1: Spinner
    private lateinit var spinner2: Spinner
    private lateinit var btnNext: Button
    private lateinit var btnBack: Button
    private var selection1: String? = null
    private var selection2: String? = null

    // Retrofit instance for API
    private lateinit var retrofit: Retrofit
    private lateinit var ganApi: GanApi

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_emotion)

        // Initialize Spinners
        spinner1 = findViewById(R.id.emotion_spinner)
        spinner2 = findViewById(R.id.intensity_spinner)

        // Set up adapter for Spinner 1
        val adapter1 = ArrayAdapter.createFromResource(
            this,
            R.array.emotions_array,
            android.R.layout.simple_spinner_item
        ).apply {
            setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        }
        spinner1.adapter = adapter1

        // Set up adapter for Spinner 2
        val adapter2 = ArrayAdapter.createFromResource(
            this,
            R.array.intensities_array,
            android.R.layout.simple_spinner_item
        ).apply {
            setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        }
        spinner2.adapter = adapter2

        // Handle selection for Spinner 1
        spinner1.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parentView: AdapterView<*>, selectedItemView: View?, position: Int, id: Long) {
                selection1 = (position + 1).toString()  // Convert position to a value (1, 2, 3, etc.)
            }

            override fun onNothingSelected(parentView: AdapterView<*>) {
                selection1 = null
            }
        }

        // Handle selection for Spinner 2
        spinner2.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parentView: AdapterView<*>, selectedItemView: View?, position: Int, id: Long) {
                selection2 = (position + 1).toString()  // Convert position to a value (1, 2, 3, etc.)
            }

            override fun onNothingSelected(parentView: AdapterView<*>) {
                selection2 = null
            }
        }

        // Initialize Buttons
        btnNext = findViewById(R.id.nextemotion_button)
        btnBack = findViewById(R.id.backemotion_button)

        // Initialize Retrofit for API calls
        initializeRetrofit()

        // Set Back button click listener
        btnBack.setOnClickListener {
            // Go back to the previous screen
            val intent = Intent(this, MainActivity::class.java) // Back button should navigate back to upload screen
            startActivity(intent)
            finish()
        }

        /* removed 4/15/25
        // Set Next button click listener
        btnNext.setOnClickListener {
            if (selection1 != null && selection2 != null) {
                // Proceed with the API call to upload the emotion and intensity selections
                uploadEmotionData()
                val intent = Intent(this, GenerateActivity::class.java) // Next button should navigate to next screen
                startActivity(intent)
                finish()
            } else {
                Toast.makeText(this, "Please select both emotion and intensity.", Toast.LENGTH_SHORT).show()
            }
        }*/

        btnNext.setOnClickListener {
            if (selection1 != null && selection2 != null) {
                // Proceed with the API call to upload the emotion and intensity selections
                uploadEmotionData()
            } else {
                // If validation fails, show a toast
                Toast.makeText(this, "Please select both emotion and intensity.", Toast.LENGTH_SHORT).show()
            }
        }

    }

    //menu toolbar logic
    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_logout -> {
                FirebaseAuth.getInstance().signOut()
                val intent = Intent(this, LoginActivity::class.java)
                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                startActivity(intent)
                true
            }

            R.id.action_readTutorial -> {
                val intent = Intent(this, ReadTutorialActivity::class.java)
                startActivity(intent)
                true
            }

            R.id.action_watchTutorial -> {
                val intent = Intent(this, WatchTutorialActivity::class.java)
                startActivity(intent)
                true
            }

            R.id.action_close -> {
                finishAffinity()
                true
            }

            else -> super.onOptionsItemSelected(item)
        }
    }
    //XXXXXXXXXXXXXXXXXXXXXXXXXX


    // Function to initialize Retrofit instance
    private fun initializeRetrofit() {
        retrofit = Retrofit.Builder()
            .baseUrl("https://close-thankfully-chow.ngrok-free.app")  // Replace with your actual server IP address
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        ganApi = retrofit.create(GanApi::class.java)
    }


    //new upload starts here and was added 1/28/2025

    private fun uploadEmotionData() {
        // Get the current Firebase user
        val user = FirebaseAuth.getInstance().currentUser
        if (user == null) {
            Toast.makeText(this, "User not authenticated.", Toast.LENGTH_SHORT).show()
            return
        }

        // Retrieve the Firebase token
        user.getIdToken(true).addOnCompleteListener { task ->
            if (task.isSuccessful) {
                val idToken = task.result?.token
                if (idToken != null) {
                    // Proceed to upload data with the token in the request headers
                    val dropdownData = DropdownInputData(
                        dropdown1 = selection1 ?: "defaultEmotion",  // Default value in case nothing is selected
                        dropdown2 = selection2 ?: "defaultIntensity"  // Default value in case nothing is selected
                    )

                    // Create a Retrofit call with the token in the headers
                    val call = ganApi.sendDropdownSelectionsWithAuth(idToken, dropdownData)

                    // Execute the call asynchronously
                    call.enqueue(object : Callback<ResponseBody> {
                        override fun onResponse(call: Call<ResponseBody>, response: Response<ResponseBody>) {
                            if (response.isSuccessful) {
                                Toast.makeText(this@EmotionActivity, "Emotion data uploaded successfully!", Toast.LENGTH_SHORT).show()
                                val intent = Intent(this@EmotionActivity, GenerateActivity::class.java)
                                startActivity(intent)
                                finish()
                            } else {
                                Toast.makeText(this@EmotionActivity, "Failed to upload emotion data.", Toast.LENGTH_SHORT).show()
                            }
                        }

                        override fun onFailure(call: Call<ResponseBody>, t: Throwable) {
                            Toast.makeText(this@EmotionActivity, "Error: ${t.message}", Toast.LENGTH_SHORT).show()
                        }
                    })
                } else {
                    Toast.makeText(this, "Failed to retrieve Firebase token.", Toast.LENGTH_SHORT).show()
                }
            } else {
                Toast.makeText(this, "Error getting Firebase token: ${task.exception?.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    //new upload ends here






    // old upload starts here
    // Function to upload emotion data (selected emotions and intensity)
//    private fun uploadEmotionData() {
//        // Create an instance of the DropdownInputData data class with the selected values
//        val dropdownData = DropdownInputData(
//            dropdown1 = selection1 ?: "defaultEmotion",  // Default value in case nothing is selected
//            dropdown2 = selection2 ?: "defaultIntensity"  // Default value in case nothing is selected
//        )
//
//        // Call the API to send the dropdown selections
//        val call = ganApi.sendDropdownSelections(dropdownData)
//
//        // Execute the call asynchronously
//        call.enqueue(object : Callback<ResponseBody> {
//            override fun onResponse(call: Call<ResponseBody>, response: Response<ResponseBody>) {
//                if (response.isSuccessful) {
//                    Toast.makeText(this@EmotionActivity, "Emotion data uploaded successfully!", Toast.LENGTH_SHORT).show()
//                    // Optionally navigate to next activity if needed
//                    // val intent = Intent(this@EmotionActivity, NextActivity::class.java)
//                    // startActivity(intent)
//                    // finish()
//                } else {
//                    Toast.makeText(this@EmotionActivity, "Failed to upload emotion data.", Toast.LENGTH_SHORT).show()
//                }
//            }
//
//            override fun onFailure(call: Call<ResponseBody>, t: Throwable) {
//                Toast.makeText(this@EmotionActivity, "Error: ${t.message}", Toast.LENGTH_SHORT).show()
//            }
//        })
//    }
//
    //old upload ends here


}