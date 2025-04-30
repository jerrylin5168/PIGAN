package com.example.piganapp

import android.content.ContentValues
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.util.Log
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.MediaController
import android.widget.ProgressBar
import android.widget.Toast
import android.widget.VideoView
import androidx.activity.ComponentActivity
import androidx.activity.result.ActivityResultCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.firebase.auth.FirebaseAuth
import okhttp3.MediaType
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.OkHttpClient
import okhttp3.RequestBody
import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.util.concurrent.TimeUnit

class GenerateActivity : AppCompatActivity() {
    // define variables for buttons, image view, and api
    private lateinit var generateButtonId: Button
    private lateinit var saveButtonId: Button // Save button for saving the output
    private lateinit var backButtonId: Button //10/29 6pm back button
    private lateinit var generatedImageViewId: VideoView //changed from ImageView to VideView 3/18/2025
    private lateinit var progressBarId: ProgressBar // 11/12 progress bar for loading animation
    private lateinit var apiService: GanApi
    private var generatedBitmap: Bitmap? = null // Hold the generated image
    private var generatedVideoFile: File? = null //hold the generated video

    private val requestWriteStorage = 1 // Request code for storage permission

//    private val requestPermissionLauncher =
//        registerForActivityResult(ActivityResultContracts.RequestPermission(), ActivityResultCallback { isGranted ->
//            if (isGranted) {
//                // Permission granted, now save the image
//                generatedBitmap?.let { bitmap ->
//                    saveImageToGallery(bitmap)
//                }
//            } else {
//                Toast.makeText(this, "Permission denied to write to external storage", Toast.LENGTH_SHORT).show()
//            }
//        })


    private val requestPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission(), ActivityResultCallback { isGranted ->
            if (isGranted) {
                // Permission granted, now save the video
                generatedVideoFile?.let { videoFile ->
                    saveImageToGallery(videoFile)
                }
            } else {
                Toast.makeText(this, "Permission denied to write to external storage", Toast.LENGTH_SHORT).show()
            }
        })





    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_generate)

        generateButtonId = findViewById(R.id.generate_button)
        saveButtonId = findViewById(R.id.save_button)
        backButtonId = findViewById(R.id.back_button) // 10/29 6pm for back button
        generatedImageViewId = findViewById(R.id.generated_image)
        progressBarId = findViewById(R.id.progress_Bar) // 11/12 progress bar setting view

        val client = OkHttpClient.Builder()
            .connectTimeout(500, TimeUnit.SECONDS) // Increase connect timeout
            .writeTimeout(500, TimeUnit.SECONDS) // Increase write timeout
            .readTimeout(500, TimeUnit.SECONDS) // Increase read timeout
            .build()

        // Set up Retrofit
        val retrofit = Retrofit.Builder()
            .baseUrl("https://close-thankfully-chow.ngrok-free.app") // IP address of computer running the server
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        apiService = retrofit.create(GanApi::class.java)

        generateButtonId.setOnClickListener {
            // show progress bar and hide other UI elements
            progressBarId.visibility = View.VISIBLE
            generateButtonId.visibility = View.GONE
            saveButtonId.visibility = View.GONE
            backButtonId.visibility = View.GONE
            generatedImageViewId.visibility = View.GONE
            // initiate image generation
            generateImage()
        }
        // 10/29 6pm, set action for back_button (navigate back to previous screen)
        backButtonId.setOnClickListener {
            val intent = Intent(this, EmotionActivity::class.java) // back button should navigate back to upload screen
            startActivity(intent)
            finish()
        }

//        saveButtonId.setOnClickListener {
//            generatedBitmap?.let { bitmap ->
//                // Check for write permission before saving
//                if (ContextCompat.checkSelfPermission(
//                        this,
//                        android.Manifest.permission.WRITE_EXTERNAL_STORAGE
//                    ) == android.content.pm.PackageManager.PERMISSION_GRANTED
//                ) {
//                    saveImageToGallery(bitmap)
//                } else {
//                    // Request permission using ActivityResult API
//                    requestPermissionLauncher.launch(android.Manifest.permission.WRITE_EXTERNAL_STORAGE)
//                }
//            } ?: run {
//                Toast.makeText(this, "No image to save!", Toast.LENGTH_SHORT).show()
//            }
//        }


        saveButtonId.setOnClickListener {
            generatedVideoFile?.let { videoFile ->
                // No need to request WRITE_EXTERNAL_STORAGE on Android 10+
                saveImageToGallery(videoFile)
            } ?: run {
                Toast.makeText(this, "No video to save!", Toast.LENGTH_SHORT).show()
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




    private fun generateImage() {
        // Retrieve the current Firebase user
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
                    // Make the API request with the Firebase token in the header
                    val requestBody = RequestBody.create("application/json".toMediaTypeOrNull(), "{}")  // Empty JSON body

                    apiService.generateImageWithAuth(idToken, requestBody).enqueue(object : Callback<ResponseBody> {
                        override fun onFailure(call: Call<ResponseBody>, t: Throwable) {
                            progressBarId.visibility = View.GONE
                            Toast.makeText(this@GenerateActivity, "Failed to generate video: ${t.message}", Toast.LENGTH_SHORT).show()
                            Log.e("GenerateVideo", "Error: ${t.message}", t)
                        }

                        override fun onResponse(call: Call<ResponseBody>, response: Response<ResponseBody>) {
                            progressBarId.visibility = View.GONE

                            if (response.isSuccessful) {
                                // Save the video file from the server
                                val videoFile = File(applicationContext.cacheDir, "generated_video.mp4")

                                try {
                                    // Save the response body (video data) to a file
                                    response.body()?.byteStream()?.use { inputStream ->
                                        FileOutputStream(videoFile).use { outputStream ->
                                            val buffer = ByteArray(4096)
                                            var bytesRead: Int
                                            while (inputStream.read(buffer).also { bytesRead = it } != -1) {
                                                outputStream.write(buffer, 0, bytesRead)
                                            }
                                        }
                                    }

                                    generatedVideoFile = videoFile // assign to the class variable

                                    // Once the video is saved, set it to the VideoView for playback
                                    val videoUri = Uri.fromFile(videoFile)
                                    val videoView: VideoView = findViewById(R.id.generated_image)
                                    videoView.setVideoURI(videoUri)

                                    // Start video playback
                                    videoView.start()

                                    // Show video controls (if any)
                                    videoView.setMediaController(MediaController(this@GenerateActivity).apply {
                                        setAnchorView(videoView)
                                    })

                                    // Show all UI elements again
                                    videoView.visibility = View.VISIBLE
                                    generateButtonId.visibility = View.VISIBLE
                                    saveButtonId.visibility = View.VISIBLE
                                    backButtonId.visibility = View.VISIBLE

                                } catch (e: Exception) {
                                    Toast.makeText(this@GenerateActivity, "Failed to save or play video: ${e.message}", Toast.LENGTH_SHORT).show()
                                }

                            } else {
                                Toast.makeText(this@GenerateActivity, "Error: ${response.message()}", Toast.LENGTH_SHORT).show()
                            }
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





    //new generate starts here, added 1/28/2025

//    private fun generateImage() {
//        // Retrieve the current Firebase user
//        val user = FirebaseAuth.getInstance().currentUser
//        if (user == null) {
//            Toast.makeText(this, "User not authenticated.", Toast.LENGTH_SHORT).show()
//            return
//        }
//
//        // Retrieve the Firebase token
//        user.getIdToken(true).addOnCompleteListener { task ->
//            if (task.isSuccessful) {
//                val idToken = task.result?.token
//                if (idToken != null) {
//                    // Make the API request with the Firebase token in the header
//                    val requestBody = RequestBody.create("application/json".toMediaTypeOrNull(), "{}")  // Empty JSON body
//
//                    apiService.generateImageWithAuth(idToken, requestBody).enqueue(object : Callback<ResponseBody> {
//                        override fun onFailure(call: Call<ResponseBody>, t: Throwable) {
//                            progressBarId.visibility = View.GONE
//                            Toast.makeText(this@GenerateActivity, "Failed to generate image: ${t.message}", Toast.LENGTH_SHORT).show()
//                            Log.e("GenerateImage", "Error: ${t.message}", t)
//                        }
//
//                        override fun onResponse(call: Call<ResponseBody>, response: Response<ResponseBody>) {
//                            progressBarId.visibility = View.GONE
//
//                            if (response.isSuccessful) {
//                                // Process the image if the response is successful
//                                response.body()?.byteStream()?.use { inputStream ->
//                                    val bitmap = BitmapFactory.decodeStream(inputStream)
//                                    if (bitmap != null) {
//                                        generatedBitmap = bitmap
//                                        generatedImageViewId.setImageBitmap(bitmap)
//                                        // Show all UI elements again
//                                        generatedImageViewId.visibility = View.VISIBLE
//                                        generateButtonId.visibility = View.VISIBLE
//                                        saveButtonId.visibility = View.VISIBLE
//                                        backButtonId.visibility = View.VISIBLE
//                                    } else {
//                                        Toast.makeText(this@GenerateActivity, "Failed to decode image", Toast.LENGTH_SHORT).show()
//                                    }
//                                } ?: run {
//                                    Toast.makeText(this@GenerateActivity, "No image data received", Toast.LENGTH_SHORT).show()
//                                }
//                            } else {
//                                Toast.makeText(this@GenerateActivity, "Error: ${response.message()}", Toast.LENGTH_SHORT).show()
//                            }
//                        }
//                    })
//                } else {
//                    Toast.makeText(this, "Failed to retrieve Firebase token.", Toast.LENGTH_SHORT).show()
//                }
//            } else {
//                Toast.makeText(this, "Error getting Firebase token: ${task.exception?.message}", Toast.LENGTH_SHORT).show()
//            }
//        }
//    }

    //new generate ends here 1/28/2025






    //oldest generate starts here

    // Function to generate the image by making an API request
//    private fun generateImage() {
//        val requestBody = RequestBody.create("application/json".toMediaTypeOrNull(), "{}") // Empty JSON body, 11/29 same error from before parse syncing
//        // Make the API request
//        apiService.generateImage(requestBody).enqueue(object : Callback<ResponseBody> {
//            override fun onFailure(call: Call<ResponseBody>, t: Throwable) {
//                // Hide progress bar if the request fails
//                progressBarId.visibility = View.GONE
//                Toast.makeText(this@GenerateActivity, "Failed to generate image: ${t.message}", Toast.LENGTH_SHORT).show()
//                Log.e("GenerateImage", "Error: ${t.message}", t)
//            }
//
//            override fun onResponse(call: Call<ResponseBody>, response: Response<ResponseBody>) {
//                // Hide the progress bar when the response is received
//                progressBarId.visibility = View.GONE
//
//                if (response.isSuccessful) {
//                    //process the image if the response is successful
//                    response.body()?.byteStream()?.use { inputStream ->
//                        val bitmap = BitmapFactory.decodeStream(inputStream)
//                        if (bitmap != null) {
//                            generatedBitmap = bitmap
//                            generatedImageViewId.setImageBitmap(bitmap)
//                            // show all UI elements again
//                            generatedImageViewId.visibility = View.VISIBLE // 11/ 12
//                            generateButtonId.visibility = View.VISIBLE // 11/12
//                            saveButtonId.visibility = View.VISIBLE
//                            backButtonId.visibility = View.VISIBLE // 11/12
//
//                        } else {
//                            Toast.makeText(this@GenerateActivity, "Failed to decode image", Toast.LENGTH_SHORT).show()
//                        }
//                    } ?: run {
//                        Toast.makeText(this@GenerateActivity, "No image data received", Toast.LENGTH_SHORT).show()
//                    }
//                } else {
//                    Toast.makeText(this@GenerateActivity, "Error: ${response.message()}", Toast.LENGTH_SHORT).show()
//                }
//            }
//        })
//    }

    //oldest generate ends here

    // Function to save the image to the gallery
//    private fun saveImageToGallery(bitmap: Bitmap) {
//        try {
//            // Get the Pictures directory
//            val directory = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES), "GeneratedImages")
//
//            // If directory doesn't exist, create it
//            if (!directory.exists()) {
//                directory.mkdirs()
//            }
//
//            // Create a unique file name based on the current time
//            val file = File(directory, "Generated_Image_${System.currentTimeMillis()}.png")
//
//            // Write the image to the file using FileOutputStream
//            FileOutputStream(file).use { outputStream ->
//                val success = bitmap.compress(Bitmap.CompressFormat.PNG, 100, outputStream)
//                if (success) {
//                    Toast.makeText(this, "Image saved to gallery", Toast.LENGTH_SHORT).show()
//
//                    // Notify the media scanner to add the image to the gallery
//                    sendBroadcast(
//                        Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE, Uri.fromFile(file))
//                    )
//                } else {
//                    Log.e("SaveImage", "Image compression failed")
//                    Toast.makeText(this, "Failed to save image - Compression issue", Toast.LENGTH_SHORT).show()
//                }
//            }
//        } catch (e: Exception) {
//            Log.e("SaveImage", "Exception while saving image: ${e.message}", e)
//            Toast.makeText(this, "Failed to save image due to error: ${e.message}", Toast.LENGTH_SHORT).show()
//        }
//    }

    private fun saveImageToGallery(videoFile: File) {
        try {
            // Get the content resolver to insert the video
            val contentResolver = contentResolver

            // Prepare the values for the video metadata (like title, mime type)
            val values = ContentValues().apply {
                put(MediaStore.Video.Media.DISPLAY_NAME, "Generated_Video_${System.currentTimeMillis()}.mp4")
                put(MediaStore.Video.Media.MIME_TYPE, "video/mp4")
                put(MediaStore.Video.Media.RELATIVE_PATH, Environment.DIRECTORY_MOVIES + "/GeneratedVideos")
                put(MediaStore.Video.Media.DATE_ADDED, System.currentTimeMillis() / 1000) // Current time
                put(MediaStore.Video.Media.DATE_MODIFIED, System.currentTimeMillis() / 1000) // Current time
            }

            // Insert the video into the MediaStore and get the URI
            val videoUri: Uri? = contentResolver.insert(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, values)

            // If URI is not null, write the video data to the MediaStore
            if (videoUri != null) {
                contentResolver.openOutputStream(videoUri)?.use { outputStream ->
                    // Open the video file to read its data
                    FileInputStream(videoFile).use { inputStream ->
                        val buffer = ByteArray(4096)
                        var bytesRead: Int
                        while (inputStream.read(buffer).also { bytesRead = it } != -1) {
                            outputStream.write(buffer, 0, bytesRead)
                        }
                    }
                }

                // Notify the user that the video has been saved
                Toast.makeText(this, "Video saved to gallery", Toast.LENGTH_SHORT).show()

                // Optionally, you can send a broadcast to notify the system about the new file
                sendBroadcast(Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE, videoUri))
            } else {
                Toast.makeText(this, "Failed to save video", Toast.LENGTH_SHORT).show()
            }
        } catch (e: Exception) {
            Log.e("SaveVideo", "Error while saving video: ${e.message}", e)
            Toast.makeText(this, "Failed to save video due to error: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }









}